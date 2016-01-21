import eudplib as ep
import runpy as rp
import sys
import json
import traceback


def empty():
    pass

# Load input json file

if len(sys.argv) != 2:
    print("Usage : euddraft [setting file]")
    sys.exit(1)

sfname = sys.argv[1]
settings = json.load(open(sfname, 'r'))

ifname = settings['input']
ofname = settings['output']
pluginSettingList = settings['plugins']


# Load plugins

print('---------- Loading plugins... ----------')

pluginList = {}

for pluginSetting in pluginSettingList:
    if isinstance(pluginSetting, str):
        pluginName = pluginSetting
        pluginArgs = {}

    else:
        pluginName = pluginSetting['pluginName']
        pluginArgs = pluginSetting.get('args', {})

    print('Loading plugin %s...' % pluginName)

    try:
        pluginDict = rp.run_path(
            'plugins/%s.py' % pluginName,
            pluginArgs,
            pluginName
        )

        if pluginDict:
            onPluginStart = pluginDict.get('onPluginStart', empty)
            beforeTriggerExec = pluginDict.get('beforeTriggerExec', empty)
            afterTriggerExec = pluginDict.get('afterTriggerExec', empty)
            pluginList[pluginName] = (
                onPluginStart,
                beforeTriggerExec,
                afterTriggerExec
            )

    except Exception as e:
        print('Error on loading plugin %s.' % pluginName)
        traceback.print_exc()


# Create main function


@ep.EUDFunc
def main():
    # init plugins
    for pluginName, plugin in pluginList.items():
        onPluginStart = plugin[0]
        onPluginStart()

    # do trigger loop
    if ep.EUDInfLoop()():
        for pluginName, plugin in pluginList.items():
            beforeTriggerExec = plugin[1]
            beforeTriggerExec()

        # eudplib v0.50 has bug that RunTrigTrigger don't revert Current Player
        # after RunTrigTriger call. So we have to do it manually
        currentPlayer = ep.f_getcurpl()
        ep.RunTrigTrigger()
        ep.f_setcurpl(currentPlayer)

        for pluginName, plugin in pluginList.items():
            afterTriggerExec = plugin[2]
            afterTriggerExec()

        ep.EUDDoEvents()

    ep.EUDEndInfLoop()

# Inject


print('--------- Injecting plugins... ---------')


ep.LoadMap(ifname)
ep.SaveMap(ofname, main)