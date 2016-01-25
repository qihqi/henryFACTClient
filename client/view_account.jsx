import React from 'react';

function getPayments(day, callback) {
    $.ajax({
        url: `/app/api/account_transaction/${day}`,
        success: callback
    });
}

function twoDecimalPlace(number) {
    number = Number(number);
    return number.toFixed(2);
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
        total += Number(arr[x].value);
    }
    return total;
}

var AccountTable = React.createClass({
    render: function() {
        var total_sale = sumValue(this.props.ventas);
        var total_pay = sumValue(this.props.pagos);
        var total_spent = sumValue(this.props.gastos);
        var total_turned_in = sumValue(this.props.turned_in);
        var ventas = this.props.ventas.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td className="value_col">{twoDecimalPlace(x.value)}</td>
            <td></td>
            <td></td>
            </tr>
        });
        var turned_in= this.props.turned_in.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td></td>
            <td className="value_col">{twoDecimalPlace(x.value)}</td>
            <td></td>
            <td></td>
            </tr>
        });
        var pagos = this.props.pagos.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td></td>
            <td></td>
            <td className="value_col">{twoDecimalPlace(x.value)}</td>
            <td></td>
            </tr>
        });
        var gastos = this.props.gastos.map((x) => {
            return <tr>
            <td>{x.desc}</td>
            <td></td>
            <td></td>
            <td></td>
            <td className="value_col">{twoDecimalPlace(x.value)}</td>
            </tr>
        });
        return <table>
        <tbody>
            <tr>
                <th></th>
                <th>Ventas</th>
                <th>Entrega</th>
                <th>Pagos</th>
                <th>Gastos</th>
            </tr>
            <tr>
                <th>Total</th>
                <th className='value_col'>{twoDecimalPlace(total_sale)}</th>
                <th className='value_col'>{twoDecimalPlace(total_turned_in)}</th>
                <th className='value_col'>{twoDecimalPlace(total_pay)}</th>
                <th className='value_col'>{twoDecimalPlace(total_spent)}</th>
            </tr>
            {ventas}
            {turned_in}
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
            var val = JSON.parse(result);
            console.log(val); 
            this.setState(val);
        });
        return {sales: [], spents: [], payments: [], turned_in: []};
        
    },
    render: function() {
        return <div>
            <AccountTable ventas={this.state.sales} 
                          pagos={this.state.payments} 
                          gastos={this.state.spents} 
                          turned_in={this.state.turned_in}/>
        </div>;
    }
});
