import React from 'react'
import SkyLight from 'react-skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, PriceForm, UNITS} from './CreateProduct';

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
var ProdSearcher = React.createClass({
    render: function() {
        return '';
    }
});

export var InvForm = React.createClass({
    getInitialState: function() {
        return {meta: {}, items: []};
    },
    loadClient: function() {
        console.log('i am called');
    },
    render: function() {
        return <div className="container">
            <div className="row">
                <div className="col-md-6">
                Cliente: <ItemLoader handleItem={this.loadClient}
                    url="/api/cliente/"/>
                </div>
                <div className="col-md-6">
                    {('client' in this.state.meta) ?
                        (this.state.meta.client.apellidos  + ' ' +
                         this.state.meta.client.nombres) :
                        ''
                     }
                </div>
            </div>
            <div className="row">
                <div className="col-md-12">
                Producto: <ItemLoader handleItem={this.loadClient}
                    url="/api/alm/1/producto/"/>
                </div>
            </div>
            <div className="row">
                <div className="col-md-12">
                    rows of items
                </div>
            </div>
            <div className="row">
                <div className="col-md-12">
                    total and shit
                </div>
            </div>
        </div>;
    }
});


// core object
// meta e items
// index de prod_id -> item number
