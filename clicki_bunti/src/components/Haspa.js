import React, {Component} from 'react';
import 'rc-slider/assets/index.css';

import FloorPlan from './FoorPlan.js';
import './Haspa.css';
import SelectionPicker from "./SelectionPicker";
import {ALL_CAPS, CAP_ALL, CAP_B, CAP_COLD, CAP_G, CAP_R, CAP_WARM, CAPABILITIES, MAPPINGS} from "./constants";
import HaspaPicker from "./HaspaPicker";

class Haspa extends Component {
    state = {
        showRGB: false,
        showW: false,
        showC: false,
        currentSelection: [],
        blockUnprivileged: false,
    }

    onSelectionColorChange = (color) => {
        let updates = {}
        for (const capability in color) {
            for (const lightID of this.state.currentSelection) {
                if (CAPABILITIES.hasOwnProperty(lightID) && CAPABILITIES[lightID].includes(capability)) {
                    updates[lightID + "/" + capability] = color[capability];
                }
            }
        }

        this.update(updates);
    }

    onMappingColorChange = (mappedTopic, color) => {
        let updates = {}
        for (const capability in color) {
            for (const lightID of MAPPINGS[mappedTopic]) {
                if (CAPABILITIES.hasOwnProperty(lightID) && CAPABILITIES[lightID].includes(capability)) {
                    updates[lightID + "/" + capability] = color[capability];
                }
            }
        }

        this.update(updates);
    }

    onHaspaColorChange = (color) => {
        this.onMappingColorChange("/haspa/licht", color);
    }

    onTableColorChange = (color) => {
        this.onMappingColorChange("/haspa/tisch/1", color);
    }

    onTerrasseColorChange = (color) => {
        this.onMappingColorChange("/haspa/terrasse", color);
    }

    recomputeSelectionColors = () => {
        let color = {
            "r": 0,
            "g": 0,
            "b": 0,
            "c": 0,
            "w": 0
        }
        if (this.state.currentSelection.length === 0) {
            return color
        } else if (this.state.currentSelection.length === 1) {
            for (const capability of CAPABILITIES[this.state.currentSelection[0]]) {
                const topic = this.state.currentSelection[0] + "/" + capability;
                if (!this.props.nodeState.hasOwnProperty(topic)) {
                    console.log("error, selection not present in state", topic, this.props.nodeState);
                } else {
                    color[capability] = this.props.nodeState[topic];
                }
            }
        } else {
            for (const capability of ALL_CAPS) {
                const selectionWithCap = this.state.currentSelection.filter(item => CAPABILITIES[item].includes(capability));
                let avg = selectionWithCap
                    .map(item => this.props.nodeState[item + "/" + capability])
                    .reduce((prev, curr) => prev + curr, 0) / selectionWithCap.length;
                color[capability] = Math.round(avg);
            }
        }

        return color
    }

    recomputeColors = (lights, caps) => {
        let color = {}
        for (const capability of caps) {
            const lightsWithCapability = lights.filter(item => CAPABILITIES[item].includes(capability));
            let avg = lightsWithCapability
                .map(item => this.props.nodeState[item + "/" + capability])
                .reduce((prev, curr) => prev + curr, 0) / lightsWithCapability.length;
            color[capability] = Math.round(avg);
        }

        return color
    }

    recomputeHaspaColors = () => {
        return this.recomputeColors(MAPPINGS["/haspa/licht"], [CAP_COLD, CAP_WARM])
    }

    recomputeTableColors = () => {
        return this.recomputeColors(MAPPINGS["/haspa/tisch/1"], [CAP_WARM, CAP_R, CAP_G, CAP_B])
    }

    recomputeTerrasseColors = () => {
        return this.recomputeColors(MAPPINGS["/haspa/terrasse"], [CAP_WARM, CAP_R, CAP_G, CAP_B])
    }

    onSelectionChange = (selection) => {
        if (selection.length > 0) {
            let state = {
                showW: false,
                showC: false,
                showRGB: false,
            }
            for (const lightID of selection) {
                if (CAPABILITIES.hasOwnProperty(lightID)) {
                    if (CAPABILITIES[lightID].includes(CAP_WARM)) {
                        state["showW"] |= true;
                    }
                    if (CAPABILITIES[lightID].includes(CAP_COLD)) {
                        state["showC"] |= true;
                    }
                    if (CAPABILITIES[lightID].includes(CAP_R)
                        || CAPABILITIES[lightID].includes(CAP_G)
                        || CAPABILITIES[lightID].includes(CAP_B)) {
                        state["showRGB"] |= true;
                    }
                } else {
                    console.error("invalid led ID:", lightID);
                }
            }
            this.setState(state);
        } else {
            this.setState({showRGB: false, showW: false, showC: false});
        }
        this.setState({currentSelection: selection})
    }

    onLightChange = (mappedID, capability, value) => {
        if (!MAPPINGS.hasOwnProperty(mappedID)) {
            console.error("invalid mapped light id");
            return;
        }

        for (const lightID of MAPPINGS[mappedID]) {
            this.setLightValue(lightID, capability, value);
        }
    }

    onColdChange = (mappedID, value) => {
        this.onLightChange(mappedID, CAP_COLD, value);
    }

    onWarmChange = (mappedID, value) => {
        this.onLightChange(mappedID, CAP_WARM, value);
    }

    setLightValue = (lightID, capability, value) => {
        if (!CAPABILITIES.hasOwnProperty(lightID)) {
            console.error("Invalid light ID:", lightID);
            return;
        }

        // do some sanity checking whether this light supports the given led type
        if (capability === CAP_ALL) {
            let updates = {};
            for (const item of CAPABILITIES[lightID]) {
                updates[lightID + "/" + item] = value;
            }
            this.update(updates);
        } else {
            if (CAPABILITIES[lightID].includes(capability)) {
                this.updateTopic(lightID + "/" + capability, value)
            } else {
                console.error("invalid capability for light ID:", lightID, capability);
            }
        }
    }

    turnOnSelection = () => {
        let updates = {};
        for (const lightID of this.state.currentSelection) {
            if (CAPABILITIES.hasOwnProperty(lightID)) {
                if (CAPABILITIES[lightID].includes(CAP_WARM)) {
                    updates[lightID + "/" + CAP_WARM] = 400;
                }
                if (CAPABILITIES[lightID].includes(CAP_COLD)) {
                    updates[lightID + "/" + CAP_COLD] = 100;
                }
            }
        }
        this.update(updates);
    }

    turnOffSelection = () => {
        let updates = {};
        for (const lightID of this.state.currentSelection) {
            if (CAPABILITIES.hasOwnProperty(lightID)) {
                if (CAPABILITIES[lightID].includes(CAP_WARM)) {
                    updates[lightID + "/" + CAP_WARM] = 0;
                }
                if (CAPABILITIES[lightID].includes(CAP_COLD)) {
                    updates[lightID + "/" + CAP_COLD] = 0;
                }
                if (CAPABILITIES[lightID].includes(CAP_R)) {
                    updates[lightID + "/" + CAP_R] = 0;
                }
                if (CAPABILITIES[lightID].includes(CAP_G)) {
                    updates[lightID + "/" + CAP_G] = 0;
                }
                if (CAPABILITIES[lightID].includes(CAP_B)) {
                    updates[lightID + "/" + CAP_B] = 0;
                }
            }
        }
        this.update(updates);
    }

    blockTrolls = () => {
        this.setState({blockUnprivileged: true});
        const message = {
            type: "update_troll_block",
            block_unprivileged: true
        }
        this.props.send(message)
    }

    unblockTrolls = () => {
        this.setState({blockUnprivileged: false});
        const message = {
            type: "update_troll_block",
            block_unprivileged: false
        }
        this.props.send(message)
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

    turnOnTable = () => {
        this.update({
            "/haspa/tisch/r": 160,
            "/haspa/tisch/g": 100,
            "/haspa/tisch/b": 70,
            "/haspa/tisch/w": 90
        })
    }

    turnOffTable = () => {
        this.update({
            "/haspa/tisch/r": 0,
            "/haspa/tisch/g": 0,
            "/haspa/tisch/b": 0,
            "/haspa/tisch/w": 0
        })
    }

    turnOnTerrasse = () => {
        this.update({
            "/haspa/terrasse/r": 160,
            "/haspa/terrasse/g": 100,
            "/haspa/terrasse/b": 70,
            "/haspa/terrasse/w": 90
        })
    }

    turnOffTerrasse = () => {
        this.update({
            "/haspa/terrasse/r": 0,
            "/haspa/terrasse/g": 0,
            "/haspa/terrasse/b": 0,
            "/haspa/terrasse/w": 0
        })
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
        const selectionColors = this.recomputeSelectionColors();
        const haspaColors = this.recomputeHaspaColors();
        const tableColors = this.recomputeTableColors();
        const terrasseColors = this.recomputeTerrasseColors();
        let picker = "";

        if (this.state.currentSelection.length > 0) {
            picker = <SelectionPicker
                colors={selectionColors}
                turnOn={this.turnOnSelection}
                turnOff={this.turnOffSelection}
                showRGBSlider={this.state.showRGB}
                showColdSlider={this.state.showC}
                showWarmSlider={this.state.showW}
                onChange={this.onSelectionColorChange}
                key={JSON.stringify(selectionColors)}
            />
        }

        let blockTrolls = "";
        if (this.props.isPrivileged) {
            if (this.state.blockUnprivileged) {
                blockTrolls = <div className="card mb-2">
                    <div className="card-body row justify-content-center">
                        <button className="btn btn-outline-success" onClick={this.unblockTrolls}>unblock trolls</button>
                    </div>
                </div>
            } else {
                blockTrolls = <div className="card mb-2">
                    <div className="card-body row justify-content-center">
                        <button className="btn btn-outline-danger" onClick={this.blockTrolls}>block trolls</button>
                    </div>
                </div>
            }
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
                        {blockTrolls}
                        <HaspaPicker
                            turnOffHaspa={this.turnOffHaspa}
                            turnOnHaspa={this.turnOnHaspa}
                            turnOnTable={this.turnOnTable}
                            turnOffTable={this.turnOffTable}
                            turnOnTerrasse={this.turnOnTerrasse}
                            turnOffTerrasse={this.turnOffTerrasse}
                            onHaspaChange={this.onHaspaColorChange}
                            onTableChange={this.onTableColorChange}
                            onTerrasseChange={this.onTerrasseColorChange}
                            haspaColors={haspaColors}
                            tableColors={tableColors}
                            terrasseColors={terrasseColors}
                            key={JSON.stringify({haspa: haspaColors, table: tableColors, terrasse: terrasseColors})}
                        />
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
