import React, {Component} from 'react';
import Slider from "rc-slider";
import {HuePicker} from "react-color";

class SelectionPicker extends Component {
    state = this.props.colors;

    onRGBChange = () => {

    }

    onAfterChange = () => {
        this.props.onChange({
            w: this.state.w,
            c: this.state.c,
            r: this.state.r,
            g: this.state.g,
            b: this.state.b,
        });
    }

    render() {
        return (
            <div className="card">
                <div className="card-body">
                    <span>Selection</span>
                    <button
                        className="btn btn-outline-danger ml-1 float-right"
                        onClick={this.props.turnOff}>off
                    </button>
                    <button
                        className="btn btn-outline-success ml-1 float-right"
                        onClick={this.props.turnOn}>on
                    </button>
                    <div className="mt-5">
                        {this.props.showRGBSlider ?
                            <>
                                <HuePicker
                                    onChangeComplete={this.onRGBChange}
                                />
                                <hr/>
                            </> : ""}
                        {this.props.showWarmSlider ?
                            <Slider
                                className="mt-1"
                                max={1000}
                                value={this.state.w}
                                onChange={(value) => this.setState({w: value})}
                                onAfterChange={this.onAfterChange}
                            /> : ""
                        }
                        {this.props.showColdSlider ?
                            <Slider
                                className="mt-1"
                                max={1000}
                                value={this.state.c}
                                onChange={(value) => this.setState({c: value})}
                                onAfterChange={this.onAfterChange}
                            /> : ""
                        }
                    </div>
                </div>
            </div>
        );
    }
}

export default SelectionPicker;
