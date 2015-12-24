import React from 'react';

function getPayments(day, callback) {
    $.ajax({
        url: `/app/api/sales?start=${day}&end=${day}&group_by=almacen_id`,
        success: callback
    });
}

export default React.createClass({
    getInitialState: function() {
        getPayments('2015-12-23', (result) => {
            this.setState(result);
        });
        return {};
        
    },
    render: function() {
        var result = [];
        for (var x in this.state) {
            result.push([x, this.state[x]]);
        }
        console.log(result);
        return <div>
            <p>{this.state.count}</p>
            <p>{this.state.value}</p>
            <p>{this.state.groups[0]}</p>
            <p>{this.state.groups[1]}</p>
            <p>{this.state.groups[2]}</p>
        </div>;
    }
});
