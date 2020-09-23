import React, {Component} from 'react';
import Slider from "rc-slider";
import {HuePicker} from "react-color";
import {CAP_COLD, CAP_WARM} from "./constants";

class HaspaPicker extends Component {
    state = {
        haspaColors: this.props.haspaColors,
        tableColors: this.props.tableColors,
        terrasseColors: this.props.terrasseColors
    };

    onRGBChange = () => {

    }

    onHaspaChange = (capability, value) => {
        let color = {...this.state.haspaColors};
        color[capability] = value;
        this.setState({haspaColors: color});
    }

    onTableChange = (capability, value) => {
        let color = {...this.state.tableColors};
        color[capability] = value;
        this.setState({tableColors: color});
    }

    onTerrasseChange = (capability, value) => {
        let color = {...this.state.terrasseColors};
        color[capability] = value;
        this.setState({terrasseColors: color});
    }

    onAfterHaspaChange = () => {
        this.props.onHaspaChange(this.state.haspaColors);
    }

    onAfterTableChange = () => {
        this.props.onTableChange(this.state.tableColors);
    }

    onAfterTerrasseChange = () => {
        this.props.onTerrasseChange(this.state.terrasseColors);
    }

    render() {
        return (
            <div className="card">
                <div className="card-body">
                    <div className="list-group list-group-flush">
                        <div className="list-group-item">
                            <span>Space</span>
                            <button
                                className="btn btn-outline-danger ml-1 float-right"
                                onClick={this.props.turnOffHaspa}>off
                            </button>
                            <button
                                className="btn btn-outline-success ml-1 float-right"
                                onClick={this.props.turnOnHaspa}>on
                            </button>
                            <div className="mt-4">
                                <Slider
                                    max={1000}
                                    value={this.state.haspaColors[CAP_WARM]}
                                    onChange={value => this.onHaspaChange(CAP_WARM, value)}
                                    onAfterChange={this.onAfterHaspaChange}
                                />
                                <Slider
                                    className="mt-1"
                                    max={1000}
                                    value={this.state.haspaColors[CAP_COLD]}
                                    onChange={value => this.onHaspaChange(CAP_COLD, value)}
                                    onAfterChange={this.onAfterHaspaChange}
                                />
                            </div>
                        </div>
                        <div className="list-group-item">
                            <span>Tisch</span>
                            <button
                                className="btn btn-outline-danger ml-1 float-right"
                                onClick={this.props.turnOffTable}>off
                            </button>
                            <button
                                className="btn btn-outline-success ml-1 float-right"
                                onClick={this.props.turnOnTable}>on
                            </button>
                            <HuePicker
                                className="mt-4"
                            />
                            <Slider
                                max={1000}
                                className="mt-3"
                                value={this.state.tableColors[CAP_WARM]}
                                onChange={value => this.onTableChange(CAP_WARM, value)}
                                onAfterChange={this.onAfterTableChange}
                            />
                        </div>
                        <div className="list-group-item">
                            <span>Terrasse</span>
                            <button
                                className="btn btn-outline-danger ml-1 float-right"
                                onClick={this.props.turnOffTerrasse}>off
                            </button>
                            <button
                                className="btn btn-outline-success ml-1 float-right"
                                onClick={this.props.turnOnTerrasse}>on
                            </button>
                            <HuePicker
                                className="mt-4"
                            />
                            <Slider
                                max={1000}
                                className="mt-3"
                                value={this.state.terrasseColors[CAP_WARM]}
                                onChange={value => this.onTerrasseChange(CAP_WARM, value)}
                                onAfterChange={this.onAfterTerrasseChange}
                            />
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default HaspaPicker;
