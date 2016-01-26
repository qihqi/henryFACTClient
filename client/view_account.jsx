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

var ViewCheck = React.createClass({
    render: function() {
       return <div className="row">
            <div className="col-md-6">
                <img height="100" alt="CHEQUE" src={this.props.imgcheck} />
            </div>

            <div className="col-md-3">
                <ul>
                    <li>{twoDecimalPlace(this.props.value)}</li>
                    <li>{this.props.holder}</li>
                    <li>{this.props.bank}</li>
                </ul>
            </div>
            <div className="col-md-3">
                <img height="100" alt="Papeleta de deposito" src={this.props.imgdeposit} />
            </div>
        </div>;
    }
});

var CheckList = React.createClass({
    render: function() {
        return this.props.checks.map( (x) => <ViewCheck key={x.uid} {...x} />);
    }
});

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
            <td></td>
            </tr>
        });
        return <table className="table">
            <tbody>
            <tr>
                <th></th>
                <th>Ventas</th>
                <th>Entrega</th>
                <th>Pagos</th>
                <th>Gastos</th>
                <th>DIFF</th>
            </tr>
            <tr>
                <th>Total</th>
                <th className='value_col'>{twoDecimalPlace(total_sale)}</th>
                <th className='value_col'>{twoDecimalPlace(total_turned_in)}</th>
                <th className='value_col'>{twoDecimalPlace(total_pay)}</th>
                <th className='value_col'>{twoDecimalPlace(total_spent)}</th>
                <th className='value_col'>{twoDecimalPlace(total_sale - total_turned_in - total_pay - total_spent)}</th>
            </tr>
            {ventas}
            {turned_in}
            {pagos}
            {gastos}
        </tbody></table>;
    }
});

var TotalSale = React.createClass({
    render: function() {
    }
});


export default React.createClass({
    getInitialState: function() {
        var today = new Date();
        if ('params' in this.props) {
            today = new Date(this.props.params.date);
        }
        var yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        today = today.toISOString().split('T')[0];
        yesterday = yesterday.toISOString().split('T')[0];
        getPayments(yesterday, (result) => {
            var val = JSON.parse(result);
            this.setState(val);
        });
        $.ajax({
            url: `/app/api/check?save_date=${yesterday}`,
            success: (result) => {
                this.setState({checks: JSON.parse(result)});
            }});
        $.ajax({
            url: `/app/api/check?deposit_date=${today}`,
            success: (result) => {
                this.setState({checks_to_deposit: JSON.parse(result)});
            }});
        return {sales: [], spents: [], payments: [], turned_in: [], checks: [], checks_to_deposit: []};
        
    },
    render: function() {
        return <div className="row">
            <div className="row">
                
            </div>
                
            <div className="row">
                <h3>{"要收的支票"} {this.state.checks.length ? "": ": 没有"}</h3>
            </div>
            <div className="row">
                {this.state.checks.map( (x) => <ViewCheck key={x.uid} {...x} />)}
            </div>
            <div className="row">
                <h3>{"要存的支票"} {this.state.checks_to_deposit.length ? "": ": 没有"}</h3>
            </div>
            <div className="row">
            {this.state.checks_to_deposit.map((x) => <ViewCheck key={x.uid} {...x} />)}
            </div>
            <div className="row">
            {this.state.checks_to_deposit.map((x) => <ViewCheck key={x.uid} {...x} />)}
            </div>
            <div className="row">
            <AccountTable ventas={this.state.sales} 
                          pagos={this.state.payments} 
                          gastos={this.state.spents} 
                          turned_in={this.state.turned_in}/> 
            </div>
        </div>;
    }
});
