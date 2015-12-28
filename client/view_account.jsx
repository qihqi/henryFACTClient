import React from 'react';

function getPayments(day, callback) {
    $.ajax({
        url: `/app/api/sales?start=${day}&end=${day}&group_by=almacen_id`,
        success: callback
    });
}

var ValuesTable = React.createClass({
    render: function() {
        var total = 0;
        for (var x in this.props.content) {
            total += this.props.content[x];
        }
        return <div>
            <h3>Total: {total}</h3>
            <ul>
                {this.props.keys.map((key) => <li> {key}: {this.props.content[key]} </li>)}
            </ul>
        </div>;
    }
});

function sumValue(arr) {
    var total = 0;
    for (var x in arr) {
        total += arr[x].value;
    }
    return total;
}

var AccountTable = React.createClass({
    render: function() {
        var total_sale = sumValue(this.props.ventas);
        var total_pay = sumValue(this.props.pagos);
        var total_spent = sumValue(this.props.gastos);
        var ventas = this.props.ventas.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td>{x.value}</td>
            <td></td>
            <td></td>
            </tr>
        });
        var pagos = this.props.pagos.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td></td>
            <td>{x.value}</td>
            <td></td>
            </tr>
        });
        var gastos = this.props.gastos.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td></td>
            <td></td>
            <td>{x.value}</td>
            </tr>
        });
        return <table>
        <tbody>
            <tr>
                <th></th>
                <th>Ventas</th>
                <th>Pagos</th>
                <th>Gastos</th>
            </tr>
            <tr>
                <th>Total</th>
                <th>{total_sale}</th>
                <th>{total_pay}</th>
                <th>{total_spent}</th>
            </tr>
            {ventas}
            {pagos}
            {gastos}
        </tbody></table>;
    }
});

const test = [
    {desc:'desc 1', value: 123},
    {desc:'desc 2', value: 123},
    {desc:'desc 3', value: 123},
    {desc:'desc 4', value: 123}];


export default React.createClass({
    getInitialState: function() {
        getPayments('2015-12-23', (result) => {
            this.setState(result);
        });
        return {count: 0, value: 0, groups: {}};
        
    },
    render: function() {
        return <div>
            <AccountTable ventas={test} pagos={test} gastos={test} />
        </div>;
    }
});
