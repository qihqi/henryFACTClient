import React from 'react';
import SkyLight from 'react-skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, PriceForm, UNITS} from './CreateProduct';

var PriceForm2 = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {display_name: '', price1: '', price2: '', cant: ''};
    },
    change: function(event) {
        if (event.target.name !== 'display_name') {
            if (isNaN(event.target.value)) {
                alert('Solo pueden ingresar numeros aqui');
            }
        }
    },
    render: function() {
        return <div>
            <p>Nombre a Mostrar: 
                <input name='display_name' 
                    ref='name' valueLink={this.linkState('display_name')}/> Este es lo que sale en las facturas
            </p>
            <p>precio1:     
                <input name='price1' ref='price1' valueLink={this.linkState('price1')}/></p>
            <p>precio2: 
                <input name='price2' ref='price2' valueLink={this.linkState('price2')}/></p>
            <p>cantidad mayorista: 
                <input ref='cant' name='cant' valueLink={this.linkState('cant')}/></p>
        </div>;
    }
});

export var SearchItemgroup = React.createClass({
    getInitialState: function() {
        return {'itemgroups': []};
    },
    search: function(event) {
        var prefix = this.refs.prefix.value;
        $.ajax({
            url: '/app/api/itemgroup?name-prefix=' + encodeURIComponent(prefix),
            success: (x) => {
                var result = JSON.parse(x).result;
                this.setState({'itemgroups': result});
            }
        });
    },
    viewItem: function(ig) {
    },
    addUnit: function(ig) {
        this.refs.addUnitForm.setItemgroup(ig);
        this.refs.addUnitOverlay.show();
    },
    render: function() {
        return <div className="container">
            <SkyLight 
                dialogStyles={{height: "70%"}}
                hiddenOnOverlayClicked ref="addUnitOverlay" title="Agregar Unidades">
                <CreateItem ref="addUnitForm"
                    units={UNITS}
                    pricelist={[{name: 'menorista', id: 1}, {name: 'mayorista', id: 2}]}
                    />
            </SkyLight>
            <div className="row">
                Nombre: <input ref="prefix" /> <button onClick={this.search}>Buscar</button>
            </div>
            <div className="row">
                {this.state.itemgroups.map((x) => {
                    return <div className="row">
                        <div className="col-md-2">
                            {x.prod_id} 
                        </div>
                        <div className="col-md-6">
                            <a href={'#/ig/'+x.uid}>{x.name}</a>
                        </div>
                        <div className="col-md-3">
                            <button onClick={this.addUnit.bind(this, x)}>Agregar Unidad</button>
                        </div>
                    </div>;
                })}
            </div>
        </div>;
    }
});

var CreateItem = React.createClass({
    getInitialState: function() {
        this.data = {};
        this.price = {};
        return {itemgroup:{}};
    },
    onSubmit: function(event) {
        this.data.itemgroupid = this.state.itemgroup.uid;
        this.data.prod_id = this.state.itemgroup.prod_id;

        var prices = {};
        for (var i in this.props.pricelist) {
            var pid = this.props.pricelist[i].id;
            var ref = 'price' + pid;
            var pform = this.refs[ref];
            prices[pid] = pform.state;
        }
        this.data.price = prices;
        console.log(this.data);
        var payload = JSON.stringify(this.data);
        $.ajax({
            url: '/app/api/item_with_price',
            data: payload,
            method: 'POST',
            success: (x) => {
                console.log(x);
            } 
        });
    },
    changeItem: function(event) {
        this.data[event.target.name] = event.target.value;
    },
    setPrice: function(result) {
        if (typeof this.price[result.priceid] == 'undefined') {
            this.price[result.priceid] = {};
        }
        this.price[result.priceid][result.key] = result.value;
    },
    setItemgroup: function(ig) {
        this.setState({itemgroup: ig});
        for (var i in this.props.pricelist) {
            var pid = this.props.pricelist[i].id;
            var ref = 'price' + pid;
            this.refs[ref].setState({'display_name': ig.name});
        }
    },
    render: function() {
        return <div>
        <h4>{this.state.itemgroup.prod_id} &nbsp; {this.state.itemgroup.name}</h4>
        <p>Unidad: {makeOption(this.props.units, 'unit', this.changeItem)}
        Multiplicador: <input name='multiplier' onChange={this.changeItem}/></p>
        <ul><b>Precios:</b>
            {this.props.pricelist.map((p, priceid) => {
                return <li key={''+ p.id}><b>{p.name}</b> &nbsp;&nbsp;
                    <PriceForm2 ref={'price'+p.id} itemid={0} priceid={p.id} />
                </li>;
            })}
        </ul>
        <button onClick={this.onSubmit}>Guardar</button>
        </div>;
    }
});
