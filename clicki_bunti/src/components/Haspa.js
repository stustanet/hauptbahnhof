import React, {Component} from 'react';
import FloorPlan from '../floor_plan.svg';

class Haspa extends Component {

    render() {
        return (
            <div className="container">
                <div className="row justify-content-center">
                    <h2 className="text-center mt-3">Haspa Stuff</h2>
                </div>
                <div className="row">
                    <div className="col-6">
                        <div className="list-group list-group-flush">
                            <div className="list-group-item">
                                <span>Terrasse</span>
                                <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                <button className="btn btn-outline-success ml-1 float-right">on</button>
                            </div>
                            <div className="list-group-item">
                                <span>Space</span>
                                <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                <button className="btn btn-outline-success ml-1 float-right">on</button>
                            </div>
                            <div className="list-group-item">
                                <span>Tisch 1</span>
                                <button className="btn btn-outline-danger ml-1 float-right">off</button>
                                <button className="btn btn-outline-success ml-1 float-right">on</button>
                            </div>
                        </div>
                    </div>
                    <div className="col-6">
                        <img src={FloorPlan} alt="Floor Plan" style={{width: '100%'}}/>
                        {/*<FloorPlan/>*/}
                    </div>
                </div>
            </div>
        )
    }
}

export default Haspa;
