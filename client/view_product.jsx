import React from 'react';
import SkyLight from './skylight';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, UNITS} from './CreateProduct';
import {PriceForm2} from './product';


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
            'items': [],
            'cant': []
        };
    },
    render: function() {
        console.log(this.state.cant);
        return <div>
            <ViewSingleItemPure {...this.state} />;
        </div>
    }
});

var CreateItem = React.createClass({
    getInitialState: function() {
        this.data = {};
        this.price = {};
        return {};
    },
    onSubmit: function(event) {
        this.data.itemgroupid = this.props.itemgroup.uid;
        this.data.prod_id = this.props.itemgroup.prod_id;
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
    setNames: function() {
        console.log('asdf');
        for (var i in this.props.pricelist) {
            var pid = this.props.pricelist[i].id;
            var ref = 'price' + pid;
            this.refs[ref].setState({'display_name': this.props.itemgroup.name});
        }
    },
    render: function() {
        return <div>
            <h4>{this.props.itemgroup.prod_id} &nbsp; {this.props.itemgroup.name}</h4>
            Unidad: {makeOption(this.props.units, 'unit', this.changeItem)}
            Multiplicador: <input name='multiplier' onChange={this.changeItem}/>
            <ul><b>Precios:</b>
            </ul>
                {this.props.pricelist.map((p)  => {
                    return <li key={''+ p.id}> <b>{p.name}</b> &nbsp;&nbsp;
                        <PriceForm2 ref={'price'+p.id} itemid={0} priceid={p.id} />
                    </li>;
                })}
            <button onClick={this.onSubmit}>Guardar</button>
        </div>;
    }
});

var QuantityLoader = React.createClass({
    loadQuantity: function(uid) {
        $.ajax({
            url: '/app/api/prod_quantity/' + uid,
            success: (x) => {
                var x = JSON.parse(x);
                this.setState(x);
            }
        });
    },
    getInitialState: function() {
        return {inv: [], quantity: [], itemgroup_id: 0};
    }, 
    render: function() {
        return <ul>
        { this.state.inv.map( (x) => {
             if (x.id >= 0 ) {    
              return <li>{x.nombre}: {Number(this.state.quantity[x.id] || 0)}</li>
             }
             return '';
        })}
        </ul>;
    }
});



var ViewSingleItemPure = React.createClass({
    showAddUnit: function() {
        this.refs.addUnitOverlay.show();
        this.refs.addUnitForm.setNames();
    },
    loadQuantity: function() {
        this.refs.quantityLoader.loadQuantity(this.props.prod.uid);
    },
    render: function() {
        return <div>
            <SkyLight 
                dialogStyles={{height: "70%"}}
                hiddenOnOverlayClicked ref="addUnitOverlay" title="Agregar Unidades">
                <CreateItem ref="addUnitForm"
                    itemgroup={this.props.prod}
                    units={UNITS}
                    pricelist={[{name: 'menorista', id: 1}, {name: 'mayorista', id: 2}]}
                    />
            </SkyLight>
        <div className="row">
            <div className="col-md-12">
                <h3>{this.props.prod.name}({this.props.prod.prod_id})</h3>
                <div>Descripcion: {this.props.prod.desc} </div>
                <button onClick={this.showAddUnit}>Agregar Unidad</button>
                {this.props.items.map((x) => {
                    return <div>
                            <p> <b> Por {x.unit} ({Number(x.multiplier)})</b></p>
                            <table className="table">
                            <thead>
                                <tr>
                                    <th></th>
                                    <th>Precio1</th>
                                    <th>Precio2</th>
                                    <th>Cant Mayor</th>
                                </tr>
                            </thead>
                            
                            <tbody>
                            {x.prices.map((price) => {
                                return <tr>
                                    <td>{price.almacen_id == 2 ? 'Mayorista' : 'Menorista'}</td>
                                    <td>{price.precio1 / 100}</td>
                                    <td>{price.precio2 / 100}</td>
                                    <td>{price.threshold}</td>
                                </tr>;
                            })}
                            </tbody></table>
                    </div>;
                })}
            </div>
        </div>
        <div className="row">
            <div className="col-md-12">
                <button onClick={this.loadQuantity}>Ver Cantidades</button>
                <QuantityLoader ref="quantityLoader" />
            </div>
        </div>
        </div>;
    }
});

