import React, {Component} from 'react';
import {HuePicker} from 'react-color'
import Slider from "rc-slider";
import 'rc-slider/assets/index.css';

import FloorPlan from './FoorPlan.js';
import './Haspa.css';

const CAP_WARM = "w";
const CAP_COLD = "c";
const CAP_R = "r";
const CAP_G = "g";
const CAP_B = "b";
const CAP_ALL = 'all';

const lights = {
    haspaLight1: "/haspa/licht/1",
    haspaLight2: "/haspa/licht/2",
    haspaLight3: "/haspa/licht/3",
    haspaLight4: "/haspa/licht/4",
    table1Front: "/haspa/tisch/1/vorne",
    table1Back: "/haspa/tisch/1/hinten",
    table2Front: "/haspa/tisch/2/vorne",
    table2Back: "/haspa/tisch/2/hinten",
    terasseLight1: "/haspa/terasse/1",
    terasseLight2: "/haspa/terasse/2",
    terasseLight3: "/haspa/terasse/3",
    terasseLight4: "/haspa/terasse/4",
}

const capabilities = {
    haspaLight1: ["w", "c"],
    haspaLight2: ["w", "c"],
    haspaLight3: ["w", "c"],
    haspaLight4: ["w", "c"],
    table1Front: ["w", "r", "g", "b"],
    table1Back: ["w", "r", "g", "b"],
    table2Front: ["w", "r", "g", "b"],
    table2Back: ["w", "r", "g", "b"],
    terasseLight1: ["w", "r", "g", "b"],
    terasseLight2: ["w", "r", "g", "b"],
    terasseLight3: ["w", "r", "g", "b"],
    terasseLight4: ["w", "r", "g", "b"],
}

const mappings = {
    haspa: ["haspaLight1", "haspaLight2", "haspaLight3", "haspaLight4"],
    terasse: ["terasseLight1", "terasseLight2", "terasseLight3", "terasseLight4"],
    table1: ["table1Front", "table1Back"],
}

class Haspa extends Component {

    state = {
        showRGB: false,
        showW: false,
        showC: false,
        selectionColor: {
            "r": 0,
            "g": 0,
            "b": 0,
            "c": 0,
            "w": 0
        },
        currentSelection: [],
    }

    onSelectionRGBChange = (color) => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID) && capabilities[lightID].includes(CAP_R)) {
                console.log("not implemented setting rgb values:", color);
            }
        })
    }

    onSelectionColdChange = (brightness) => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID) && capabilities[lightID].includes(CAP_COLD)) {
                this.updateTopic(lights[lightID] + "/" + CAP_COLD, brightness)
            }
        })
    }

    onSelectionWarmChange = (brightness) => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID) && capabilities[lightID].includes(CAP_WARM)) {
                this.updateTopic(lights[lightID] + "/" + CAP_WARM, brightness)
            }
        })
    }

    setSelectionColor = (capability, value) => {
        let update = {};
        update[capability] = value;
        this.setState({selectionColor: Object.assign(this.state.selectionColor, update)})
    }

    recomputeSelectionColors = (selection) => {
        if (selection.length === 0) {
            this.setState({
                selectionColor: {
                    "r": 0,
                    "g": 0,
                    "b": 0,
                    "c": 0,
                    "w": 0
                }
            });
        } else if (selection.length === 1) {
            let updatedColor = {...this.state.selectionColor};
            for (const capability of capabilities[selection[0]]) {
                const topic = lights[selection[0]] + "/" + capability;
                if (!this.props.nodeState.hasOwnProperty(topic)) {
                    console.log("error, selection not present in state", topic, this.props.nodeState);
                } else {
                    updatedColor[capability] = this.props.nodeState[topic];
                }
            }
            console.log(updatedColor)
            this.setState({selectionColor: updatedColor})
        } else {
            let updatedColor = {...this.state.selectionColor};
            for (const capability of capabilities[selection[0]]) {
                const selectionWithCap = selection.filter(item => capabilities[item].includes(capability));
                let avg = selectionWithCap
                    .map(item => this.props.nodeState[lights[item] + "/" + capability])
                    .reduce((prev, curr) => prev + curr, 0) / selectionWithCap.length;
                updatedColor[capability] = Math.round(avg);
            }
            console.log(updatedColor)
            this.setState({selectionColor: updatedColor})
        }
    }

    onSelectionChange = (selection) => {
        if (selection.length > 0) {
            let state = {
                showW: false,
                showC: false,
                showRGB: false,
            }
            selection.forEach((lightID) => {
                if (capabilities.hasOwnProperty(lightID)) {
                    if (capabilities[lightID].includes(CAP_WARM)) {
                        state["showW"] |= true;
                    }
                    if (capabilities[lightID].includes(CAP_COLD)) {
                        state["showC"] |= true;
                    }
                    if (capabilities[lightID].includes(CAP_R)
                        || capabilities[lightID].includes(CAP_G)
                        || capabilities[lightID].includes(CAP_B)) {
                        state["showRGB"] |= true;
                    }
                } else {
                    console.error("invalid led ID:", lightID);
                }
            })
            this.setState(state);
        } else {
            this.setState({showRGB: false, showW: false, showC: false});
        }
        this.recomputeSelectionColors(selection);
        this.setState({currentSelection: selection})
    }

    onLightChange = (mappedID, capability, value) => {
        if (!mappings.hasOwnProperty(mappedID)) {
            console.error("invalid mapped light id");
            return;
        }

        mappings[mappedID].forEach((lightID) => {
            this.setLightValue(lightID, capability, value);
        })
    }

    onColdChange = (mappedID, value) => {
        this.onLightChange(mappedID, CAP_COLD, value);
    }

    onWarmChange = (mappedID, value) => {
        this.onLightChange(mappedID, CAP_WARM, value);
    }

    setLightValue = (lightID, capability, value) => {
        if (!lights.hasOwnProperty(lightID) || !capabilities.hasOwnProperty(lightID)) {
            console.error("Invalid light ID:", lightID);
            return;
        }

        // do some sanity checking whether this light supports the given led type
        if (capability === CAP_ALL) {
            let updates = {};
            capabilities[lightID].forEach((item) => {
                updates[lights[lightID] + "/" + item] = value;
            });
            this.update(updates);
        } else {
            if (capabilities[lightID].includes(capability)) {
                this.updateTopic(lights[lightID] + "/" + capability, value)
            } else {
                console.error("invalid capability for light ID:", lightID, capability);
            }
        }
    }

    turnOnSelection = () => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID)) {
                let updates = {};
                if (capabilities[lightID].includes(CAP_WARM)) {
                    updates[lights[lightID] + "/" + CAP_WARM] = 400;
                }
                if (capabilities[lightID].includes(CAP_COLD)) {
                    updates[lights[lightID] + "/" + CAP_COLD] = 100;
                }
                this.update(updates);
            }
        })
    }

    turnOffSelection = () => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID)) {
                let updates = {};
                if (capabilities[lightID].includes(CAP_WARM)) {
                    updates[lights[lightID] + "/" + CAP_WARM] = 0;
                }
                if (capabilities[lightID].includes(CAP_COLD)) {
                    updates[lights[lightID] + "/" + CAP_COLD] = 0;
                }
                if (capabilities[lightID].includes(CAP_R)) {
                    updates[lights[lightID] + "/" + CAP_R] = 0;
                }
                if (capabilities[lightID].includes(CAP_G)) {
                    updates[lights[lightID] + "/" + CAP_G] = 0;
                }
                if (capabilities[lightID].includes(CAP_B)) {
                    updates[lights[lightID] + "/" + CAP_B] = 0;
                }
                this.update(updates);
            }
        })
    }

    turnOnHaspa = () => {
        this.update({
            "/haspa/licht/w": 400,
            "/haspa/licht/c": 100,
            "/haspa/licht/tisch": 1,
            "/haspa/tisch/r": 160,
            "/haspa/tisch/g": 100,
            "/haspa/tisch/b": 70,
            "/haspa/tisch/w": 90
        })
    }

    turnOffHaspa = () => {
        this.updateTopic("/haspa/licht", 0)
    }

    updateTopic = (topic, value) => {
        let updates = {}
        updates[topic] = value
        this.update(updates)
    }

    update = (updates) => {
        const payload = {
            type: "state_update",
            updates: {
                nodes: updates
            }
        }
        this.props.send(payload)
    }

    render() {
        let picker = "";

        if (this.state.currentSelection.length > 0) {
            picker =
                <div className="card">
                    <div className="card-body">
                        <span>Selection</span>
                        <button
                            className="btn btn-outline-danger ml-1 float-right"
                            onClick={this.turnOffSelection}>off
                        </button>
                        <button
                            className="btn btn-outline-success ml-1 float-right"
                            onClick={this.turnOnSelection}>on
                        </button>
                        <div className="mt-5">
                            {this.state.showRGB ?
                                <>
                                    <HuePicker
                                        onChangeComplete={this.onSelectionRGBChange}
                                    />
                                    <hr/>
                                </> : ""}
                            {this.state.showW ?
                                <Slider
                                    className="mt-1"
                                    max={1000}
                                    value={this.state.selectionColor[CAP_WARM]}
                                    onChange={(value) => this.setSelectionColor(CAP_WARM, value)}
                                    onAfterChange={this.onSelectionWarmChange}
                                /> : ""
                            }
                            {this.state.showC ?
                                <Slider
                                    className="mt-1"
                                    max={1000}
                                    value={this.state.selectionColor[CAP_COLD]}
                                    onChange={(value) => this.setSelectionColor(CAP_COLD, value)}
                                    onAfterChange={this.onSelectionColdChange}
                                /> : ""
                            }
                        </div>
                    </div>
                </div>
        }

        return (
            <div className="container">
                <div className="row mt-3">
                    <div className="col-12 justify-content-center">
                        <FloorPlan
                            preserveAspectRatio="xMinYMin"
                            width="100%"
                            onSelectionChange={this.onSelectionChange}
                        />
                    </div>
                </div>
                <div className="row">
                    <div className="col-6">
                        <div className="card">
                            <div className="card-body">
                                <div className="list-group list-group-flush">
                                    <div className="list-group-item">
                                        <span>Space</span>
                                        <button
                                            className="btn btn-outline-danger ml-1 float-right"
                                            onClick={this.turnOffHaspa}>off
                                        </button>
                                        <button
                                            className="btn btn-outline-success ml-1 float-right"
                                            onClick={this.turnOnHaspa}>on
                                        </button>
                                        <div className="mt-4">
                                            <Slider
                                                max={1000}
                                                onAfterChange={(value) => {
                                                    this.onWarmChange("haspa", value)
                                                }}
                                            />
                                            <Slider
                                                className="mt-1"
                                                max={1000}
                                                onAfterChange={(value) => {
                                                    this.onColdChange("haspa", value)
                                                }}
                                            />
                                        </div>
                                    </div>
                                    <div className="list-group-item">
                                        <span>Tisch 1</span>
                                        <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                        <button className="btn btn-outline-success ml-1 float-right">on</button>
                                        <HuePicker
                                            className="mt-4"
                                        />
                                        <Slider
                                            max={1000}
                                            className="mt-3"
                                            onAfterChange={(value) => {
                                                this.onWarmChange("haspa", value)
                                            }}
                                        />
                                    </div>
                                    <div className="list-group-item">
                                        <span>Terrasse</span>
                                        <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                        <button className="btn btn-outline-success ml-1 float-right">on</button>
                                        <HuePicker
                                            className="mt-4"
                                        />
                                        <Slider
                                            className="mt-3"
                                            max={1000}
                                            onAfterChange={(value) => {
                                                this.onWarmChange("haspa", value)
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col-6">
                        {picker}
                    </div>
                </div>
            </div>
        )
    }
}

export default Haspa;
