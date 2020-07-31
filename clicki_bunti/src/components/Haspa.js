import React, {Component} from 'react';
import {SliderPicker} from 'react-color'
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
                this.publish(lightID, CAP_COLD, brightness);
            }
        })
    }

    onSelectionWarmChange = (brightness) => {
        this.state.currentSelection.forEach((lightID) => {
            if (capabilities.hasOwnProperty(lightID) && capabilities[lightID].includes(CAP_WARM)) {
                this.publish(lightID, CAP_WARM, brightness);
            }
        })
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
                    if (capabilities[lightID].includes(CAP_R) || capabilities[lightID].includes(CAP_G) || capabilities[lightID].includes(CAP_B)) {
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
        this.setState({currentSelection: selection});
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
            capabilities[lightID].forEach((item) => {
                this.publish(lightID, item, value)
            });
        } else {
            if (capabilities[lightID].includes(capability)) {
                this.publish(lightID, capability, value);
            } else {
                console.error("invalid capability for light ID:", lightID, capability);
            }
        }
    }

    turnOnHaspa = () => {
        this.props.publish("/haspa/licht/w", 400);
        this.props.publish("/haspa/licht/c", 100);
        this.props.publish("/haspa/licht/tisch", 1);
        this.props.publish("/haspa/tisch/r", 160);
        this.props.publish("/haspa/tisch/g", 100);
        this.props.publish("/haspa/tisch/b", 70);
        this.props.publish("/haspa/tisch/w", 90);
    }

    publish = (lightID, capability, value) => {
        this.props.publish(lights[lightID] + "/" + capability, value);
    }

    render() {
        let picker = "";

        if (this.state.currentSelection.length > 0) {
            picker =
                <div className="card">
                    <div className="card-body">
                        <span>Selection</span>
                        <button className="btn btn-outline-danger ml-1 float-right">off</button>
                        <button className="btn btn-outline-success ml-1 float-right">on</button>
                        <div className="mt-5">
                            {this.state.showRGB ?
                                <>
                                    <SliderPicker
                                        color={this.state.color}
                                        onChangeComplete={this.onSelectionRGBChange}
                                    />
                                    <hr/>
                                </> : ""}
                            {this.state.showW ?
                                <Slider
                                    className="mt-1"
                                    max={1000}
                                    onAfterChange={this.onSelectionWarmChange}
                                /> : ""
                            }
                            {this.state.showC ?
                                <Slider
                                    className="mt-1"
                                    max={1000}
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
                                            onClick={() => {
                                                this.props.publish("/haspa/licht", 0)
                                            }}>off
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
                                        <SliderPicker
                                            className="mt-4"
                                        />
                                        <Slider
                                            max={1000}
                                            className="mt-3"
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
                                    <div className="list-group-item">
                                        <span>Terrasse</span>
                                        <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                        <button className="btn btn-outline-success ml-1 float-right">on</button>
                                        <SliderPicker
                                            className="mt-4"
                                        />
                                        <Slider
                                            className="mt-3"
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
