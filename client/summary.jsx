import React from 'react';
import {twoDecimalPlace} from './view_account';

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

var ShowDailySale = React.createClass({
    getInitialState: function() {
        this.getTotals();
        return {totals: []};
    },
    getTotals: function() {
        $.ajax({
            url: `/app/api/sales?start=${this.props.date}&end=${this.props.date}`,
            success: (x) => {
                var result = JSON.parse(x);
                this.setState({totals: result.result});
            }
        });
    },
    render: function() {
        var mayorista = 0;
        var menorista = 0;
        for (var i in this.state.totals) {
            var item = this.state.totals[i];
            if (item[0] == 1 || item[0] == 3) {
                menorista += Number(item[1]);
            } else if (item[0] == 2) {
                mayorista += Number(item[1]);
            }
        }
        return <ul>
            <li>Mayorista {'批发'}: {twoDecimalPlace(mayorista)}</li>
            <li>Menorista {'零售'}: {twoDecimalPlace(menorista)}</li>
        </ul>;
    }
});

var ShowAccountDeposit = React.createClass({
    render: function() {
        var make_row = (x) => {
            var row = [x.date, x.desc, -x.value];
            var img =(x.img && x.img.length > 0) ? <img height="200" src={x.img} /> : "";
            var key = x.uid ? x.uid : x.desc;
            var result = [
                <tr key={key} className={x.type}>
                    {row.map((x) => {
                        if (typeof(x) === 'number') 
                            return <td className="value_col">{x}</td>
                        return <td>{x}</td>;
                    })}
                </tr>];
            if (x.img && x.img.length > 0) {
                result.push(<tr><td colSpan="3"><img height="200" src={x.img} /></td></tr>);
            }
            return result;
        };
        return <div>
            <table className="table">
            <tbody>
            <tr>
                <th>Fecha</th>
                <th>Desc</th>
                <th>Valor</th>
            </tr>
            {this.props.account_deposits.map(make_row)}
        </tbody></table></div>;
    }
});



export var Summary = React.createClass({
    getInitialState: function() {
        var today = new Date();
        var yesterday = new Date(today);
        if (today.getDay() == 1) { // Monday {
            yesterday.setDate(today.getDate() - 2);
        } else {
            yesterday.setDate(today.getDate() - 1);
        }
        var week = new Date(today);
        week.setDate(today.getDate() - 7);
        today = today.toISOString().split('T')[0];
        yesterday = yesterday.toISOString().split('T')[0];
        week = week.toISOString().split('T')[0];
        this.getAllAccountDeposit();
        this.getChecks(week, today);
        return {today: today, yesterday: yesterday,
            with_deposit: [], without_deposit: [], checks: []};
    },
    getAllAccountDeposit: function() {
        $.ajax({
            url: '/app/api/account_deposit_with_img',
            success: (x) => {
                var result = JSON.parse(x);
                this.setState(result);
            }
        });
    }, 
    getChecks: function(start, end) {
        $.ajax({
            url: `/app/api/check?deposit_date=${start}&deposit_date_end=${end}`,
            success: (x) => {
                var result = JSON.parse(x);
                this.setState({'checks': result.result});
            }
        });
    },
    render: function() {
        return <div className="container">
            <div className="row">
                <div className="col-md-6">
                    <div className="row">
                        <div className="col-md-6">
                            Ventas de Hoy ({this.state.today}):
                            <ShowDailySale date={this.state.today} />
                        </div>
                        <div className="col-md-6">
                            Ventas de Ayer ({this.state.yesterday}):
                            <ShowDailySale date={this.state.yesterday} />
                        </div>
                    </div>
                    <div className="row"><h4>CHEQUES PARA HOY</h4></div>
                    {this.state.checks.map( (x) => <ViewCheck key={x.uid} {...x} />)}
                    <div className="row">
                        <h4>Ultimos Depositos</h4>
                        {this.state.without_deposit.length > 0 ?
                            <ShowAccountDeposit account_deposits={this.state.without_deposit} />
                            : 'NO HAY'}
                    </div>
                    <div className="row">
                        <h4>Ultimos Papeletas Ingresados</h4>
                        {this.state.with_deposit.length > 0 ? 
                            <ShowAccountDeposit account_deposits={this.state.with_deposit} />
                            : 'NO HAY'}
                    </div>
                </div>
            </div>
        </div>
    }
});

