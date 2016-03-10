import React from 'react';
import SkyLight from 'react-skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, PriceForm} from './CreateProduct';

export var ViewSingleItem = React.createClass({
    loadProduct: function() {
        $.ajax({
            url: '/app/api/item_full/' + this.props.params.itemgroupid,
            success: (x) => {
                var obj = JSON.parse(x);
                this.setState(obj);
            }
        });
    },
    getInitialState: function() {
        this.loadProduct();
        return {
            'prod': {prod_id: '', name: '', desc: ''},
            'items': []
        };
    },
    render: function() {
        return <ViewSingleItemPure {...this.state} />;
    }
});


var ViewSingleItemPure = React.createClass({
    render: function() {
        return <div>
            <ul>
                <li>Codigo: {this.props.prod.prod_id} </li>
                <li>Nombre: {this.props.prod.name} </li>
                <li>Descripcion: {this.props.prod.desc} </li>
                <li>Unidades:
                    {this.props.items.map((x) => {
                        return <ul>
                            <li>Unidad: {x.unit}</li>
                            <li>Multiplicador: {x.multiplier}</li>
                            <li>Precios:
                                {x.prices.map((price) => {
                                    return <div>
                                        <p>{price.almacen_id == 1 ? 'Menorista' : 'Mayorista'}</p>
                                        <p>{price.precio1 / 100}</p>
                                        <p>{price.precio2 / 100}</p>
                                    </div>;
                                })}
                            </li>
                        </ul>;
                    })}
                </li>
            </ul>
        </div>;
    }
});

