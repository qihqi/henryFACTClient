import React from 'react';

export var UNITS = ['', 'YARDA', 'METRO', 'ROLLO', 'PAQ.PEQUENO', 'PAQ.GRANDE', 'UNIDAD', 'TIRA'];

export function makeOption(options, name, onchange) {
    return <select name={name} onChange={onchange}>
    {options.map((x)=>{
       return <option defaultValue={x}>{x}</option>;
    })}
    </select>;
}

export var PriceForm = React.createClass({
    change: function(event) {
        if (event.target.name !== 'display_name') {
            if (isNaN(event.target.value)) {
                alert('Solo pueden ingresar numeros aqui');
                return;
            }
        }
        var result = {
            itemid: this.props.itemid,
            priceid: this.props.priceid,
            key: event.target.name,
            value: event.target.value
        };
        this.props.setPrice(result);
    },
    render: function() {
        return <div>
    <p>Nombre a Mostrar: <input name='display_name' ref='name' onChange={this.change}/> Este es lo que sale en las facturas</p>
    <p>precio1: <input name='price1' ref='price1' onChange={this.change}/></p>
    <p>precio2: <input name='price2' ref='price2' onChange={this.change}/></p>
    <p>cantidad mayorista: <input ref='cant' name='cant' onChange={this.change}/></p>
    </div>;
    }
});

var CreateProdForm = React.createClass({
    getInitialState: function() {
        this.items = [{
            unit: '',
            multiplier: 1,
            prices: {}
        }];
        this.prices = [];
        return {
            items: [{
                unit: '',
                multiplier: 1
            }],
        };
    },
    addItem: function(event) {
        event.preventDefault();
        var newItems = this.state.items;
        newItems.push({
            unit: '',
            multiplier: 1,
        });
        this.items.push({
            unit: '',
            multiplier: 1,
            prices: {}
        });
        this.setState({items: newItems});
    },
    deleteItem: function(event) {
        event.preventDefault();
        var newItems = this.state.items;
        newItems.pop();
        this.items.pop();
        this.setState({items: newItems});
    },
    save: function() {
        var result = {
            prod: {
                name: this.refs.name.value,
                prod_id: this.refs.prod_id.value
            },
            items: this.items
        }
        console.log(JSON.stringify(result));
        var self = this;
        $.ajax({
            url: '/app/api/item_full',
            data: JSON.stringify(result),
            method: 'POST',
            success: function(msg) {
                if (msg.status == 'success') {
                    alert('sucess');
                    self.clear();
                } else {
                    alert(msg.msg);
                }

            },
        });
    },
    setPrice(result) {
        var item = this.items[result.itemid];
        if (!(result.priceid in item.prices)) {
            item.prices[result.priceid] = {};
        }
        item.prices[result.priceid][result.key] = result.value;
    },
    changeItem: function(key, event) {
        this.items[key][event.target.name] = event.target.value;
    },
    clear: function() {
        location.reload();
    },
    render: function() {
        console.log(this.props.pricelist);
        return <div>
            <p>Codigo: <input type="text" ref='prod_id'/></p>
            <p>Nombre: <input type="text" ref='name'/> Este es el nombre que sale en transferencias</p> 
            <h4>Unidades:</h4>
            {this.state.items.map((x, key) => {
                return <div key={key}>
                <p>Unidad: {makeOption(this.props.units, 'unit', this.changeItem.bind(this, key))}
                Multiplicador: <input name='multiplier' onChange={this.changeItem.bind(this, key)}/></p>
                <ul><b>Precios:</b>
                {this.props.pricelist.map((p, priceid) => {
                    return <li key={''+ p.id+key}><b>{p.name}</b> &nbsp;&nbsp;
                        <PriceForm ref={'item' + key} setPrice={this.setPrice}
                        itemid={key} priceid={p.id} />
                    </li>;
                })}
            </ul>
            </div>;
            })}
        <button onClick={this.addItem}>MAS UNIDAD</button>
        <button onClick={this.deleteItem}>MENOS UNIDAD</button>
        <button onClick={this.save}>GUARDAR</button>
        </div>;
    }
});

export var ProdApp = React.createClass({
    getInitialState() {
        return {
        'units': ['', 'YARDA', 'METRO', 'ROLLO', 'PAQ.PEQUENO', 'PAQ.GRANDE', 'UNIDAD', 'TIRA'],
        pricelist: [{name: 'menorista', id: 1}, {name: 'mayorista', id: 2}]};
    },
    render: function() {
        return <div className="container">
            <div className="row"><h3>Crear Producto</h3></div>
            <div className="row">
                <CreateProdForm units={this.state.units} pricelist={this.state.pricelist} />
            </div>
        </div>;
    },
});
