import React, {Component} from 'react';

class Loading extends Component {

    render() {
        return (
            <div className="container">
                <div className="col-md-6 m-auto">
                    <div className="card card-body mt-5">
                        <h2 className="text-center">... Loading ...</h2>
                    </div>
                </div>
            </div>
        )
    }
}

export default Loading;
