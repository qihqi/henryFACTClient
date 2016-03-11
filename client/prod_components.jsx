import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import ReactDOM from 'react-dom';

export function makeOption(options, name, onchange) {
    return <select name={name} onChange={onchange}>
    {options.map((x)=>{
       return <option value={x.val}>{x.name}</option>;
    })}
    </select>;
}


var ProdLoader = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {prod_id: null, cant: null, name: '', price: '', subtotal: ''};
    },
    handleCodigo: function(event) {
        if (event.key == 'Enter') {
            $.ajax({
                // url: '/app/api/itemgroup?prod_id='+encodeURIComponent(this.refs.codigo.value),
                url: '/static/product_test',
                success: (x) => {
                    var result = JSON.parse(x).result;
                    if (result.length > 0) {
                        this.setState({name: result[0].name});
                        this.refs.cant.getDOMNode().focus();
                    }
                }
            });
        }
    },
    handleCant: function(event) {
        if (event.key == 'Enter') {
            this.props.addItem(this.state);
            this.setState(this.getInitialState());
            this.refs.codigo.getDOMNode().focus();
        }
    },
    render: function() {
        return <div className="row">
            <input placeholder="Codigo" ref='codigo' valueLink={this.linkState('prod_id')} onKeyPress={this.handleCodigo}/>
            <input placeholder="Cantidad" ref='cant' valueLink={this.linkState('cant')} onKeyPress={this.handleCant}/>
            {this.state.name}
            {this.state.price}
            {this.state.subtotal}
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
    render: function() {
        return <div className="container">
            <div className="row">
              Desde: {makeOption([{val:1, name:'almacen'}, {val:2, name:'bodega'}], 'origin', this.addOption.bind(this))}
              Hasta: {makeOption(['almacen', 'bodega'], 'dest', this.addOption.bind(this))}
            </div>
            <div className="row">
                <ProdLoader addItem={this.addItem} />
            </div>
            <div className="row">
            <table className="table"><tbody>
                {this.state.items.map((c, index) => {
                    return <tr>
                        <td>{c.prod.prod_id}</td>
                        <td>{c.cant}</td>
                        <td>{c.prod.name}</td>
                        <td><button onClick={this.removeItem.bind(this, index)}>Borrar</button></td>
                    </tr>;
                })}
            </tbody></table>;
            </div>
        </div>
    }
});

ReactDOM.render(<App />, document.getElementById('content'));
