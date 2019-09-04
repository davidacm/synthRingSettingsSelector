# -*- coding: UTF-8 -*-
# Synth ring settings selector: This add-on allows the user to select which     settings should appear on the synth settings ring.
# Copyright (C) 2019 David CM
# Author: David CM <dhf360@gmail.com>
# Released under GPL 2
#globalPlugins/synthRingSettingsSelector.py

import buildVersion, config, globalPluginHandler, globalVars, gui, synthDriverHandler, wx, addonHandler

addonHandler.initTranslation()

SETTINGS_ID = 'id'
SETTINGS_AVAILABLE  = 'availableInSettingsRing'

confspec = {
	"availableSettings": "string_list(default=list('language', 'voice', 'variant', 'rate', 'rateBoost', 'volume', 'pitch', 'inflection'))"
}
config.conf.spec["synthRingSettingsSelector"] = confspec

#saves the original setSynth function
origSetSynth = synthDriverHandler.setSynth

# alternate function to setSynth.
def setSynth(name,isFallback=False):
	# return temporally to the original function because that function sometimes calls itself, and we don't want our function to be called.
	synthDriverHandler.setSynth = origSetSynth
	r = origSetSynth(name,isFallback)
	synthDriverHandler.setSynth = setSynth
	if r: setAvailableSettings()
	return r

def setAvailableSettings():
	if synthDriverHandler._curSynth and globalVars.settingsRing:
		for s in synthDriverHandler._curSynth.supportedSettings:
			setattr(s, SETTINGS_AVAILABLE, True if getattr(s, SETTINGS_ID) in config.conf['synthRingSettingsSelector']['availableSettings'] else False)
		globalVars.settingsRing.updateSupportedSettings(synthDriverHandler._curSynth)

class SynthRingSettingsSelectorSettingsPanel(gui.SettingsPanel):
	# Translators: This is the label for the Synth ring settings selector  settings category in NVDA Settings screen.
	title = _("Synth ring settings selector")

	def makeSettings(self, settingsSizer):
		self.curSettings = config.conf['synthRingSettingsSelector']['availableSettings']
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is a label with instructions for the user.
		sHelper.addItem(wx.StaticText(self, label =_("Check the settings that you want to include in the Synth settings ring")))
		# Translators: This is a label for a group of options.
		settingsGroup = gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label= _("Settings group")), wx.VERTICAL))
		sHelper.addItem(settingsGroup)
		self.settingsCheckbox = {}
		for k in synthDriverHandler._curSynth.supportedSettings:
			self.settingsCheckbox[getattr(k, SETTINGS_ID)] = settingsGroup.addItem(wx.CheckBox(self, label =k.displayNameWithAccelerator))
			self.settingsCheckbox[getattr(k, SETTINGS_ID)].SetValue(getattr(k, SETTINGS_ID) in self.curSettings)

	def onSave(self):
		newSettings = []
		keys = self.settingsCheckbox.keys()
		for k in keys:
			if self.settingsCheckbox[k].GetValue(): newSettings.append(k)
		[newSettings.append(k) for k in self.curSettings if k not in keys]
		config.conf['synthRingSettingsSelector']['availableSettings'] = newSettings
		config.post_configProfileSwitch.notify()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		global SETTINGS_AVAILABLE, SETTINGS_ID
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		if buildVersion.version_year*10 +buildVersion.version_major < 20192:
			SETTINGS_ID = 'name'
			SETTINGS_AVAILABLE = 'availableInSynthSettingsRing'
		synthDriverHandler.setSynth = setSynth
		gui.settingsDialogs.setSynth = setSynth
		self.handleConfigProfileSwitch()
		config.post_configProfileSwitch.register(self.handleConfigProfileSwitch)
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SynthRingSettingsSelectorSettingsPanel)

	def handleConfigProfileSwitch(self):
		setAvailableSettings()

	def terminate(self):
		super(GlobalPlugin, self).terminate()
		synthDriverHandler.setSynth = origSetSynth
		gui.settingsDialogs.setSynth = origSetSynth
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SynthRingSettingsSelectorSettingsPanel)
		config.post_configProfileSwitch.unregister(self.handleConfigProfileSwitch)