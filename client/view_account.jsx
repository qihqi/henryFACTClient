import React from 'react';
import SkyLight from 'react-skylight';

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
        var make_row = (x) => {
            var row = [x.date, x.desc, x.value, '', twoDecimalPlace(x.saldo), x.img];
            if (x.value < 0) {
                row = [x.date, x.desc, '', x.value, twoDecimalPlace(x.saldo), x.img];
            }
            return <tr>
                {row.map((x) => {
                    if (typeof(x) === 'number') 
                        return <td className="value_col">{x}</td>
                    return <td>{x}</td>;
                })}
            </tr>;
        };
        return <table className="table">
            <tbody>
            <tr>
                <th>Fecha</th>
                <th>Desc</th>
                <th>Ingreso</th>
                <th>Egreso</th>
                <th>Saldo</th>
                <th></th>
            </tr>
            {this.props.all_events.map(make_row)}
        </tbody></table>;
    }
});

var InputDeposit = React.createClass({
    submit: function(event) {
        event.preventDefault();
        var data = {
            date: this.refs.date.value,
            value: Number(this.refs.value.value),
            account : this.refs.account.value
        };
        this.props.onSubmit(data);
    },
    render: function() {
        return <form onSubmit={this.submit}>
            <p>Fecha:<input ref='date' /></p>
            <p>Valor:<input ref='value' /></p>
            <p>Cuenta: <select> 
                {this.props.account_options.map(
                    (x)=><option value={x.uid}>{x.name}</option>)}
            </select></p>
            <p><input type="submit" value="Guardar" /></p>
        </form>
    }
});

var TotalSale = React.createClass({
    render: function() {
    }
});


export default React.createClass({
    getBankAccounts: function() {
        var x = $.ajax({
            url: '/app/api/bank_account',
            success: function(r) {
                this.setState({'bank': r.result});
            }.bind(this),
            failure: function(r) {
                alert('err');
            }
        });
    },
    getAccountInfo: function(start_date, end_date) {
        $.ajax({
            url: `/app/api/account_transaction?start=${start_date}&end=${end_date}`,
            success: (result) => {
                var val = JSON.parse(result);

                var all_events = val.sales.concat(  
                                 val.payments,  
                                 val.turned_in,
                                 val.spents);
                var sorted = all_events.sort((a, b) => {
                    if (a.date > b.date) return 1;
                    if (a.date < b.date) return -1;
                    if (a.type > b.type) return -1;
                    if (a.type < b.type) return 1;
                    return 0;
                });
                var start = 0;
                for (var x in sorted) {
                    sorted[x].value = Number(sorted[x].value);
                    start += sorted[x].value;
                    sorted[x].saldo = start;
                }
                this.setState({'all_events': sorted, 'balance': start});
            }});
    },
    getInitialState: function() {
        var today = new Date();
        today.setDate(today.getDate() - 1);
        if ('params' in this.props && 'date' in this.props.params) {
            today = new Date(this.props.params.date);
        }
        var yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 7);
        today = today.toISOString().split('T')[0];
        yesterday = yesterday.toISOString().split('T')[0];
        this.getAccountInfo(yesterday, today);
        this.getBankAccounts();
        return {'all_events': [], 'bank': []};
        
    },
    newDates: function() {
        var start_date = this.refs.start_date.value;
        var end_date = this.refs.end_date.value;
        this.getAccountInfo(start_date, end_date);
    },
    saveInputDeposit: function(result) {
        var newitem = result;
        newitem.type = 'turned_in';
        newitem.img = '';
        newitem.desc = 'DEPOSITO/ENTREGA';
        newitem.value = -newitem.value;
        $.ajax({
            url: '/app/api/acct_transaction',
            method: 'POST',
            data: JSON.stringify(newitem),
            success: function(result) {
                alert(result.pkey);
            }
        });
        this.balance = result.value + this.state.balance;
        result.saldo = this.balance;
        this.setState({'all_events': this.state.all_events.concat(newitem)});
    },
    render: function() {
        return <div className="row">
            <div className="row"> 
                <button onClick={()=>this.refs.inputDeposit.show()}>Ingresar Deposito</button>
                <SkyLight hiddenOnOverlayClicked ref="inputDeposit" title="Ingresar Deposito">
                    <InputDeposit onSubmit={this.saveInputDeposit} account_options={this.state.bank}/>
                </SkyLight>
            </div>
            <div className="row">
                Desde:<input ref='start_date' /> Hasta: <input ref='end_date' /> 
                <button onClick={this.newDates}>Cargar</button>
            </div>
            <div className="row">
            <AccountTable all_events={this.state.all_events} />
            </div>
        </div>;
    }
});
