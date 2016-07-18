import React from 'react';
import SkyLight from './skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, PriceForm, UNITS} from './CreateProduct';

export var PriceForm2 = React.createClass({
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
    mixins: [LinkedStateMixin],
    searchProduct: function(prefix) {
        $.ajax({
            url: '/app/api/itemgroup?name-prefix=' + encodeURIComponent(prefix),
            success: (x) => {
                var result = JSON.parse(x).result;
                this.setState({'itemgroups': result, term: prefix});
            }, 
            failure: (x) => {
                alert('No pudo encontrar producto');
                this.setState({term: prefix});
            }
        });
    },
    getInitialState: function() {
        if (this.props.params.search_term) {
            var prefix = this.props.params.search_term;
            this.searchProduct(prefix);
        }
        return {'itemgroups': []};
    },
    search: function(event) {
        window.location = '#/view_prod/' + this.state.term;
        this.searchProduct(this.state.term);
    },
    viewItem: function(ig) {
    },
    addUnit: function(ig) {
        this.refs.addUnitForm.setItemgroup(ig);
        this.refs.addUnitOverlay.show();
    },
    render: function() {
        return <div className="container">
            <h3>Buscar Producto</h3>
            <div className="row">
                Nombre: <input ref="prefix" valueLink={this.linkState('term')}/> 
                <button onClick={this.search}>Buscar</button>
            </div>
            <div className="row">
                <div className="row">
                    <div className="col-md-2 header">
                        No. Item
                    </div>
                    <div className="col-md-2 header">
                        Codigo
                    </div>
                    <div className="col-md-6 header">
                        Nombre
                    </div>
                </div>
                {this.state.itemgroups.map((x) => {
                    return <div className="row">
                        <div className="col-md-2">
                            {x.uid} 
                        </div>
                        <div className="col-md-2">
                            {x.prod_id} 
                        </div>
                        <div className="col-md-6">
                            <a href={'#/ig/'+x.uid}>{x.name}</a>
                        </div>
                    </div>;
                })}
            </div>
        </div>;
    }
});

