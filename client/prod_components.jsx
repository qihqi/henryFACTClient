import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import ReactDOM from 'react-dom';
import twoDecimalPlace from './view_account';

export function makeOption(options, name, onchange) {
    return <select name={name} onChange={onchange}>
    {options.map((x)=>{
       return <option value={x.val}>{x.name}</option>;
    })}
    </select>;
}

var ItemLoader = React.createClass({
    handle: function(event) {
        var codigo = encodeURIComponent(this.refs.codigo.value);
        if (event.key == 'Enter') {
            $.ajax({
                url: this.props.url + codigo,
                success: (x) => {
                    var result = JSON.parse(x);
                    this.props.handleItem(codigo, result);
                }
            });
        }
    },
    render: function() {
        return <span>
    <input placeholder="Codigo" ref='codigo' onKeyPress={this.handle} /></span> ;
    }
});

var ClientLoader = React.createClass({
    getInitialState: function() {
        return {apellidos: '', nombre: ''};
    },
    handleCodigo: function(codigo, content) {
        this.setState(content);
        this.props.loadClient(content);
    },
    render: function() {
        return <div className="row">
            <ItemLoader url='/api/cliente/' handleItem={this.handleCodigo} />
            {this.state.apellidos + ' ' + this.state.nombre}
        </div>
    }
});


var ProdLoader = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {prod: {}, cant: ''};
    },
    handleCodigo: function(codigo, content) {
        this.setState({prod: content});
            
    },
    handleCant: function(event) {
        if (event.key == 'Enter') {
            this.props.addItem(this.state);
            this.setState(this.getInitialState());
            this.refs.codigo.getDOMNode().focus();
        }
    },
    render: function() {
        var price = twoDecimalPlace(this.state.prod.precio1/100);
        var subtotal = Number(this.state.cant) * price;
        return <div className="row">
            <ItemLoader url='/api/alm/1/producto/' handleItem={this.handleCodigo} />
            <input placeholder="Cantidad" ref='cant' valueLink={this.linkState('cant')} onKeyPress={this.handleCant}/>
            <span>{this.state.prod.nombre}</span>
            <span>{price}</span>
            <span>{subtotal}</span>
        </div>
    }
});

var ItemGroupCantList = React.createClass({
    render: function() {
        return <table className="table"><tbody>
            {this.props.items.map((c) => {
                return <tr>
                    <td>{c.prod_id}</td>
                    <td>{c.cant}</td>
                    <td>{c.name}</td>
                </tr>;
            })}
        </tbody></table>;
    }
});

  var _db_attr = {
        'uid': 'id',
        'origin': 'origin',
        'dest': 'dest',
        'user': 'user',
        'trans_type': 'trans_type',
        'ref': 'ref',
        'timestamp': 'timestamp',
        'status': 'status',
        'value': 'value'};

var App = React.createClass({
    getInitialState: function() {
        return {'items': [], meta: {}};
    },
    addItem: function(item) {
        var newItem = {prod: item, cant: item.cant};
        delete newItem.prod.cant;
        this.state.items.push(newItem);
        this.setState({items: this.state.items});
    },
    removeItem: function(position) {
        this.state.items.splice(position, 1);
        this.setState({items: this.state.items});
    },
    addOption: function(op) {
        this.state.meta[op.target.name] = op.target.value;
    },
    loadClient: function(client) {
        console.log(client);
    },
    render: function() {
        return <div className="container">
            <div className="row">
                Cliente: <ClientLoader loadedClient={this.loadClient}/>
            </div>
            <div className="row">
                Cargar Producto: <ProdLoader addItem={this.addItem} />
            </div>
            <div className="row">
            <table className="table">
            <thead>
                <tr>
                    <th>Codigo</th>
                    <th>Cantidad</th>
                    <th>Nombre</th>
                    <th>Precio</th>
                    <th>Subtotal</th>
                    <th></th>
                </tr>
            </thead> 
            <tbody>
                {this.state.items.map((c, index) => {
                    return <tr>
                        <td>{c.prod.prod_id}</td>
                        <td>{c.cant}</td>
                        <td>{c.prod.name}</td>
                        <td></td>
                        <td></td>
                        <td><button onClick={this.removeItem.bind(this, index)}>Borrar</button></td>
                    </tr>;
                })}
            </tbody></table>
            </div>
        </div>;
    }
});

ReactDOM.render(<App />, document.getElementById('content'));
