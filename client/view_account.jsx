import React from 'react';
import SkyLight from 'react-skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';

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
    uploadImageForm: function(x) {
        this.props.showImgForm(x.uid);
    },
    showEditForm: function(x, _) {
        this.props.showEditForm(x);
    },
    render: function() {
        var make_row = (x) => {
            var row = [x.date, x.desc, x.value, '', twoDecimalPlace(x.saldo)];
            if (x.value < 0) {
                row = [x.date, x.desc, '', x.value, twoDecimalPlace(x.saldo)];
            }
            var img =(x.img && x.img.length > 0) ? <img height="100" src={x.img} /> : "";
            var button = (x.type == 'turned_in') 
                    ? <div> 
                        <p><button onClick={this.uploadImageForm.bind(this, x)}>Agregar Papeleta</button></p>
                        <p><button onClick={this.showEditForm.bind(this, x)}>Editar</button></p>
                      </div>
                    : "";
            var key = x.uid ? x.uid : x.desc;
            return <tr key={key}>
                {row.map((x) => {
                    if (typeof(x) === 'number') 
                        return <td className="value_col">{x}</td>
                    return <td>{x}</td>;
                })}
                <td>{img}</td>
                <td className="noprint">{button}</td>
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
                <th></th>
            </tr>
            {this.props.all_events.map(make_row)}
        </tbody></table>;
    }
});

var InputDeposit = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {'date': '', 'to_bank_account': -1, 'value': ''};
    },
    submit: function(event) {
        event.preventDefault();
        console.log(Date.parse(this.refs.date.value));
        if (! (/\d{4}-\d{2}-\d{2}/.test(this.refs.date.value))) {
            alert('ingrese fecha en formato YYYY-MM-DD');
            return;
        }
        var data = {
            date: this.refs.date.value,
            value: Number(this.refs.value.value),
            to_bank_account : this.refs.account.value
        };
        if ('uid' in this.state) {
            data.uid = this.state.uid;
        }
        this.props.onSubmit(data);
    },
    render: function() {
        return <form onSubmit={this.submit}>
            <p>Fecha:<input valueLink={this.linkState('date')} ref='date' placeholder="YYYY-MM-DD"/></p>
            <p>Valor:<input ref='value'  valueLink={this.linkState('value')} placeholder="valor"/></p>
            <p>Cuenta: <select ref='account' valueLink={this.linkState('to_bank_account')}> 
                {this.props.account_options.map(
                    (x)=><option key={x.uid} value={x.uid}>{x.name}</option>)}
            </select></p>
            <p><input type="submit" value="Guardar"/></p>
        </form>
    }
});

var TotalSale = React.createClass({
    render: function() {
    }
});

var Papeleta = React.createClass({
    setUid: function(uid) {
        this.uid = uid;
    },
    submit: function(e) {
        var fd = new FormData();    
        var imgFile = this.refs.file.getDOMNode().files[0];
        
        fd.append('img', imgFile);
        fd.append('objtype', 'account_transaction');
        fd.append('objid', this.uid);
        console.log(this.uid);
        fd.append('replace', true);
        $.ajax({
            url: '/app/api/attachimg',
            data: fd,
            processData: false,
            contentType: false,
            type: 'POST',
            success: (data) => {
                this.props.onSubmit(this.uid, data.url);
            }
        });
        e.preventDefault()
    },
    render: function() {
        return <form method="post" action="/app/attachimg" 
                     encType="multipart/form-data" onSubmit={this.submit}>
            Imagen Deposito:
            <input ref='file' type="file" name="img"/> <input type="submit" />
        </form>;
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
                var val = JSON.parse(result).result;
                var sorted = val.sort((a, b) => {
                    if (a.date > b.date) return 1;
                    if (a.date < b.date) return -1;
                    if (a.type > b.type) return -1;
                    if (a.type < b.type) return 1;
                    return 0;
                });
                var start = 0;
                this.index_by_uid = {};
                for (var x in sorted) {
                    sorted[x].value = Number(sorted[x].value);
                    start += sorted[x].value;
                    sorted[x].saldo = start;
                    this.index_by_uid[sorted[x].uid] = x;
                }
                this.setState({'all_events': sorted, 'balance': start,
                               'start_date': start_date, 'end_date': end_date});
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
        return {'all_events': [], 'bank': [], 'start_date': '', 'end_date': ''};
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
            success: (pkey) => {
                this.balance = result.value + this.state.balance;
                newitem.saldo = this.balance;
                newitem.uid = pkey.pkey;
                this.index_by_uid[newitem.uid] = this.state.all_events.length;
                this.setState({'all_events': this.state.all_events.concat(newitem)});
            }
        });
    },
    editInputDeposit: function(result) {
        var newitem = Object.assign(result);
        newitem.value = -Number(newitem.value);
        var uid = newitem.uid;
        delete newitem['uid'];
        $.ajax({
            url: '/app/api/acct_transaction/' + uid,
            method: 'PUT',
            data: JSON.stringify(newitem),
            success: (result) => {
                if (result.updated == 1) {
                    var index = this.index_by_uid[uid];
                    console.log(this.index_by_uid, index);
                    var array = this.state.all_events;
                    array[index] = Object.assign(array[index], newitem);
                    this.setState({'all_events': array});
                    this.refs.editInputDeposit.hide();
                }
            }
        });
    },
    showImgForm: function(obj) {
        console.log('showImgForm', obj);
        this.refs.papeleta.setUid(obj);
        this.refs.imgForm.show();
    },
    submitPapeleta: function(uid, url) {
        var array = this.state.all_events;
        var index = this.index_by_uid[uid];
        array[index].img = url;
        this.setState({'all_events': array});
        this.refs.imgForm.hide();
    },
    showEditForm: function(current_object) {
        var newobj = Object.assign({}, current_object);
        newobj.value = -newobj.value;
        this.refs.editDepositForm.setState(newobj);
        this.refs.editDeposit.show();
    },
    render: function() {
        return <div className="row">
            <h3>{this.state.start_date} -- {this.state.end_date} </h3>
            <SkyLight hiddenOnOverlayClicked ref="inputDeposit" title="Ingresar Deposito">
                <InputDeposit onSubmit={this.saveInputDeposit} account_options={this.state.bank}/>
            </SkyLight>
            <SkyLight hiddenOnOverlayClicked ref="imgForm" title="Papeleta">
                <Papeleta ref="papeleta" onSubmit={this.submitPapeleta}/>
            </SkyLight>
            <SkyLight hiddenOnOverlayClicked ref="editDeposit" title="Editar Deposito">
                <InputDeposit ref="editDepositForm" onSubmit={this.editInputDeposit} account_options={this.state.bank}/>
            </SkyLight>
            <div className="row noprint"> 
                <button onClick={()=>this.refs.inputDeposit.show()}>Ingresar Deposito</button>
            </div>
            <div className="row noprint">
                Desde:<input ref='start_date' /> Hasta: <input ref='end_date' /> 
                <button onClick={this.newDates}>Cargar</button>
            </div>
            <div className="row">
            <AccountTable all_events={this.state.all_events} 
                showImgForm={this.showImgForm}
                showEditForm={this.showEditForm} />
            </div>
        </div>;
    }
});
