import QtQuick 2.7
import QtQml.StateMachine 1.0 as DSM

DSM.StateMachine {
    initialState: sites_state
    running: true

    property alias sites_state: sites_state
    property alias drops_state: drops_state
    property alias gear_performance_state: gear_performance_state
    property alias hooks_state: hooks_state

//    property bool full_species_list_selected: false

    signal to_sites_state
    signal to_drops_state
    signal to_gear_performance_state
    signal to_hooks_state

    DSM.State {
        id: sites_state
        onEntered: {
            if (screens.busy) { return; }
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "sites"

            console.log('sites_state - previous = ' + stateMachine.previousScreen + ', current = ' + stateMachine.screen);

            if (stateMachine.previousScreen === "drops") {
                screens.pop();
                stateMachine.drop = null;
                stateMachine.dropOpId = null;
                stateMachine.anglerAOpId = null;
                stateMachine.anglerBOpId = null;
                stateMachine.anglerCOpId = null;
                stateMachine.angler = null;
                stateMachine.hook = null;
            }
        }
        DSM.SignalTransition {
            targetState: drops_state
            signal: to_drops_state
        } // to_drops_state
    } // sites_state
    DSM.State {
        id: drops_state
        onEntered: {
            if (screens.busy) { return; }
            stateMachine.previousScreen = stateMachine.screen
            stateMachine.screen = "drops"

            console.log('drops_state - previous = ' + stateMachine.previousScreen + ', current = ' + stateMachine.screen);

            if (stateMachine.previousScreen === "sites") {
                screens.push(Qt.resolvedUrl("DropsScreen.qml"));
                drops.selectOperationAttributes(stateMachine.setId)
            } else if ((stateMachine.previousScreen === "hooks") || (stateMachine.previousScreen === "gear_performance")) {
                screens.pop();
            }
            stateMachine.angler = null;
            stateMachine.hook = null;

        }
        DSM.SignalTransition {
            targetState: sites_state
            signal: to_sites_state
        } // to_sites_state
        DSM.SignalTransition {
            targetState: gear_performance_state
            signal: to_gear_performance_state
        } // to_gear_performance_state
        DSM.SignalTransition {
            targetState: hooks_state
            signal: to_hooks_state
        } // to_hooks_state
    } // drop_state
    DSM.State {
        id: gear_performance_state
        onEntered: {
            if (stateMachine.screen == "hooks") {
                screens.pop()  // #143: pop hooks off stack so Drops stays second in line
            }
            stateMachine.previousScreen = stateMachine.screen;
            stateMachine.screen = "gear_performance"
//            stateMachine.angler = null;
            screens.push(Qt.resolvedUrl("GearPerformanceScreen.qml"));
            gearPerformance.selectGearPerformance();
        }
        DSM.SignalTransition {
            targetState: drops_state
            signal: to_drops_state
        } // to_drops_state
        DSM.SignalTransition {  // #143: enable transition to hooks from gp
            targetState: hooks_state
            signal: to_hooks_state
        } // to_hooks_state
    } // gear_performance_state
    DSM.State {
        id: hooks_state
        onEntered: {
            if (stateMachine.screen === "gear_performance") {
                screens.pop()  // #143: pop gp off stack so Drops stays second in line
            }
            stateMachine.previousScreen = stateMachine.screen;
            stateMachine.screen = "hooks"
            screens.push(Qt.resolvedUrl("HooksScreen.qml"));
            hooks.selectHooks();
        }
        DSM.SignalTransition {
            targetState: drops_state
            signal: to_drops_state
        } // to_drops_state
        DSM.SignalTransition {  // #143: enable transition to gp from hooks
            targetState: gear_performance_state
            signal: to_gear_performance_state
        } // to_drops_state
    } // hook_state
}