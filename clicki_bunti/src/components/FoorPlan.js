import React, {Component} from "react";
import "./FloorPlan.css";

class FloorPlan extends Component {
    state = {
        currentSelection: []
    }

    onClick = (e) => {
        e.preventDefault();
        const rect = e.target;
        if (rect.style["stroke"] === "rgba(0, 0, 0, 0.5)") {
            rect.style["stroke"] = "#38ff00";
        } else {
            rect.style["stroke"] = "rgba(0, 0, 0, 0.5)";
        }

        if (this.state.currentSelection.includes(rect.id)) {
            this.state.currentSelection.splice(this.state.currentSelection.indexOf(rect.id), 1);
        } else {
            this.state.currentSelection.push(rect.id);
        }

        this.props.onSelectionChange(this.state.currentSelection);
    }

    render() {
        return (
            // <FloorPlanSVG preserveAspectRatio="xMinYMin" width="100%"/>
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="100%"
                viewBox="17 24 260 160"
                id="floor_plan"
                preserveAspectRatio="xMinYMin">
                <g
                    transform="rotate(90,145.49678,146.23274)"
                    id="layer1">
                    <rect
                        id="rect10"
                        width="155.46429"
                        height="253.10437"
                        x="24.060163"
                        y="17.564341"
                        style={{
                            fill: "none",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: "0.5",
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1
                        }}/>
                    <path
                        style={{
                            fill: "none",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.499325,
                            strokeLinecap: "butt",
                            strokeLinejoin: "miter",
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1
                        }}
                        d="m 179.78002,106.53859 -155.393183,-0.002 41.073592,-29.133762 c 0,0 8.740111,8.320071 8.710397,28.972712"
                        id="path837"/>
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.445647,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="haspaLight2"
                        width="78.131027"
                        height="5.9563074"
                        x="101.40936"
                        y="106.52479"
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.534717,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="haspaLight1"
                        width="5.5919604"
                        height="76.206718"
                        x="173.92145"
                        y="112.48885"
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.456191,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="haspaLight4"
                        width="5.6121798"
                        height="76.805298"
                        x="173.90607"
                        y="188.68773"
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.475457,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="haspaLight3"
                        width="78.954239"
                        height="5.1752009"
                        x="100.57021"
                        y="265.4935"
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "none",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.499999,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1
                        }}
                        id="rect851"
                        width="93.442627"
                        height="38.435867"
                        x="24.060501"
                        y="204.0271"/>
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.518802,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="table1Back"
                        width="46.643314"
                        height="4.4506459"
                        x="24.067804"
                        y="220.92178"
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.494494,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="table1Front"
                        width="44.437176"
                        height="4.285027"
                        x="73.059784"
                        y="220.90677"
                        onClick={this.onClick}
                    />
                    <rect
                        y="29.342463"
                        x="24.095457"
                        height="5.9563074"
                        width="83.748718"
                        id="terasseLight2"
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.46139,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        onClick={this.onClick}
                    />
                    <rect
                        y="65.076042"
                        x="24.067871"
                        height="5.9563074"
                        width="83.872177"
                        id="terasseLight1"
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.46173,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        onClick={this.onClick}
                    />
                    <rect
                        y="29.325666"
                        x="107.82738"
                        height="5.9898973"
                        width="71.708618"
                        id="terasseLight4"
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.42814,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        onClick={this.onClick}
                    />
                    <rect
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.42788,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        id="terasseLight3"
                        width="71.617996"
                        height="5.9901586"
                        x="107.93975"
                        y="65.042496"
                        onClick={this.onClick}
                    />
                    <rect
                        y="143.82944"
                        x="24.061581"
                        height="38.435867"
                        width="93.442627"
                        id="rect851-7"
                        style={{
                            fill: "none",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.499999,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1
                        }}/>
                    <rect
                        y="160.72412"
                        x="24.068886"
                        height="4.4506459"
                        width="46.643314"
                        id="table2Back"
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.518803,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        onClick={this.onClick}
                    />
                    <rect
                        y="160.70911"
                        x="73.06086"
                        height="4.285027"
                        width="44.437176"
                        id="table2Front"
                        style={{
                            fill: "#ffffff",
                            stroke: "rgba(0,0,0,0.5)",
                            strokeWidth: 0.494493,
                            strokeMiterlimit: 4,
                            strokeDasharray: "none",
                            strokeOpacity: 1,
                            fillOpacity: 1
                        }}
                        onClick={this.onClick}
                    />
                </g>
            </svg>
        )
    }
}

export default FloorPlan;
