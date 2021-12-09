import copy
import json
import os

import boto3
import requests
import traceback

from .template import Template, InvalidTemplateException, RetrieveTemplateException, TemplateNotFound
from .templateprocessor import TemplateProcessor
from .ruleengine import RuleEngine
from .utils import handle_exception


class Forwarder(object):
  
  def __init__(self, logger):
    self.logger = logger    

    self.confpath = self._get_env("CONFIGPATH")
    self.templatepath = self._get_env("TEMPLATEPATH")
    self.region = self._get_env("AWS_REGION")

    self._ssm = boto3.client("ssm", region_name=self.region)

    try:
      v = self._ssm.get_parameter(Name=self.confpath)
      _config = v["Parameter"]["Value"]
      self.config = json.loads(_config)
      self.logger.info(json.dumps(self.config))
    except Exception as e:
      self.logger.critical("Failed to retrieve configuration")
      raise e

    self.templates = {}

    if "rules" in self.config:
      self.ruleengine = RuleEngine(self.config["rules"])
    else:
      self.ruleengine = None


  def _get_env(self, varname):
    val = os.environ.get(varname)
    if val is None:
      self.logger.critical(f"Environment variable {varname} is not set")
      raise Exception(f"No {varname}")
    return val


  def _get_profile(self, data):
    if "profile" not in data:
      data["profile"] = "default" 

    profile = self.config["profiles"].get(data["profile"])

    if profile.get("endpoint") is None:
      self.logger.critical("Profile {} does not have endpoint defined".format(data["profile"]))
      raise Exception("No endpoint for profile")

    profile["name"] = data["profile"]

    return profile


  def _get_template(self, profile):
    templatename = profile["template"] if "template" in profile else "default"

    if templatename in self.templates:
      return self.templates[templatename]
    
    path = f"{self.templatepath}/{templatename}"

    try:
      t = Template(ssmclient=self._ssm, path=path)
      self.templates[templatename] = t
      return t
    except TemplateNotFound:
      exception_text = "ERROR - Could not find template {t}!\n\nMessage:\n{{= datastr =}}\n\n".format(t=path)
    except (InvalidTemplateException, RetrieveTemplateException):
      estr = traceback.format_exc()
      exception_text = "ERROR - Exception:\n{ex}\n\nMessage:\n{{= datastr =}}\n\n".format(ex=estr)
    return Template(text = exception_text)


  def _get_message(self, record, profile, msgtemplate):

    try:
      idata = json.loads(record["body"])
    except TypeError:
      # Not valid json, so process as a single value
      idata = record["body"]

    profileparams = profile["parameters"] if "parameters" in profile else None

    text = TemplateProcessor.process(msgtemplate, data = idata)

    if isinstance(profileparams, dict):
      # process as json message
      msg = copy.deepcopy(profileparams)
      for k, v in profileparams.items():
        if v == '@@@@':
          msg[k] = text
          break
      return json.dumps(msg)
    else:
      # process as plain text
      return text
        
    
  def _send_message(self, msg, endpoint):
    r = requests.post(endpoint, data = msg)
    return r


  def _check_rules(self, record):
    j = json.loads(record["body"])

    if self.ruleengine is not None:  
      r = self.ruleengine.evaluate(j)
      if r is not None:
        return r

    return { "body": j }


  def handle(self, event):
    for record in event["Records"]:
      try:
        data = self._check_rules(record)
        profile = self._get_profile(data)
        msgtemplate = self._get_template(profile)
        msg = self._get_message(data, profile, msgtemplate)
        endpoint = profile.get("endpoint")

        self.logger.info("profile: {}".format(profile.get("name")))
        self.logger.info(f"msg: {msg}")
        r = self._send_message(msg, endpoint)

        if r.status_code != 200:
          txt = "Failed to send message. Statuscode={sc}, profile={pn}, msg={m}".format(
            sc = r.status_code,
            pn = profile.get("name"),
            m  = msg
          )
          raise Exception(txt)
      except Exception as e:
        handle_exception(self.logger, e)
