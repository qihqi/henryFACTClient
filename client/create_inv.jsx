import React from 'react'
import ReactDOM from 'react-dom';
import SkyLight from 'react-skylight'; 
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import {makeOption, PriceForm, UNITS} from './CreateProduct';

var IVA_PERCENT = 14;
function focusRef(ref) {
    var dom = ReactDOM.findDOMNode(ref);
    dom.focus();
    dom.select();
}

var ItemLoader = React.createClass({
    handle: function(event) {
        var codigo = encodeURIComponent(this.refs.codigo.value);
        if (event.key == 'Enter') {
            console.log('here');
            $.ajax({
                url: this.props.url + codigo,
                success: (x) => {
                    var result = JSON.parse(x);
                    this.props.handleItem(codigo, result);
                }
            });
        }
    },
    focus: function() {
        focusRef(this.refs.codigo);
    },
    setValue: function(val) {
        var dom = ReactDOM.findDOMNode(this.refs.codigo);
        dom.value = val;
    },
    render: function() {
        return <span>
        <input size={this.props.size} 
        placeholder="Codigo" ref='codigo' onKeyDown={this.handle} /></span> ;
    }
});

// need url as props
var Searcher = React.createClass({
    getInitialState: function() {
        return {result: []};
    },
    focus: function() {
        console.log('focus serach term');
        focusRef(this.refs.search_term);
    },
    performSearch: function() {
        var term = this.refs.search_term.value;
        $.ajax({
            url: this.props.url + term,
            success: (result) => {
                result = JSON.parse(result);
                this.setState({'result': result});
            }
        });
    },
    maybeSearch: function(event) {
        if (event.key == 'Enter') {
            this.performSearch();
        }
    },
    clicked: function(index) {
        console.log(index);
        var prod = this.state.result[index];
        this.props.onSelectItem(prod.codigo, prod);
    },
    render: function() {
        return <div style={{height: '80%'}}>
            <input ref="search_term" onKeyDown={this.maybeSearch} /> 
            <button className="btn btn-sm btn-primary" onClick={this.performSearch}>Buscar</button>
            <ul className="list-group" style={{'overflow-y': 'scroll', height: '100%'}}>
                {this.state.result.map( (x, index) => {
                    return <li className="list-group-item" key={index} onClick={this.clicked.bind(this, index)}>
                        ({x.codigo}) {this.props.display(x)}
                    </li>;
                })}
            </ul>
        </div>;
    }
});

var ItemAndCant = React.createClass({
    render: function() {
        return <table className="table" >
            <tbody>
                {this.props.items.map((x) => 
                    <tr>
                        <td className="col-md-1">{x.prod.codigo}</td>
                        <td className="col-md-8">{x.prod.nombre}</td>
                        <td className="col-md-1 value_col">{x.cant}</td>
                        <td className="col-md-1 value_col">{x.prod.precio1 / 100}</td>
                        <td className="col-md-1 value_col">{x.prod.precio1 * x.cant / 100}</td>
                    </tr>
                )}
            </tbody>
        </table>;
    }
});

export var LoginForm = React.createClass({
    login: function() {
        var data = {
            username: this.refs.username.value,
            password: this.refs.password.value,
        };
        $.ajax({
            url: '/api/authenticate',
            method: 'POST',
            data: data,
            success: this.props.callback
        });
    },
            
    render: function() {
        return <div className="form-signin">
            <h3>Pedidos</h3>
            <input placeholder="Usuario" className="form-control" ref="username" />
            <input placeholder="Clave" className="form-control" type="password" ref="password" />
            <button className="btn btn-lg btn-primary btn-block" onClick={this.login}>
                Entrar</button>
        </div>;
    }

});

const searchStyles = {
    width: '70%',
    height: '80%',
    marginTop: '-300px',
    marginLeft: '-35%',
};

function computeTotals(items) {
    var subtotal = 0;
    var desc = 0;
    var cant_mayorista = 0;
    for (var x in items) {
        var x = items[x];
        subtotal += (x.cant * x.prod.precio1);
        cant_mayorista = Number(x.prod.cant_mayorista);
        if (cant_mayorista >= 1000) {
            cant_mayorista = cant_mayorista / 1000;
        }
        if (x.cant >= cant_mayorista) {
            desc += x.cant * (x.prod.precio1 - (x.prod.precio2 || x.prod.precio1));     
        }
    }
    var subs = subtotal - desc;
    var iva = Math.round(IVA_PERCENT * subs / 100 );
    var total = subs + iva;
    return {
        subtotal:subtotal,
        discount: desc,
        tax: iva,
        total: total
    };
}


var InvFormContent = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {
            codigo: this.props.user.last_factura,
            user: {}, 
            client: null,
            meta: {almacen_id: 1},
            items: [],
            current_prod: null,
            current_cant: 0,
            paid_amount: 0,
            payment_format: 'EFECTIVO'
        };
    },
    loadClient: function(uid, result) {
        if (result) {
            this.setState({client: result});
            this.refs.input_client.setValue(uid);
            this.refs.input_prod.focus();
        }
        else { 
            this.refs.input_client.focus();
        }
    },
    loadClientSearch: function(uid, result) {
        this.loadClient(uid, result);
        this.refs.searchClient.hide();
    },
    loadProd: function(uid, result) {
        if (result) {
            var dom = ReactDOM.findDOMNode(this.refs.input_cant);
            dom.focus();
            dom.select();
            this.refs.input_prod.setValue(uid);
            this.setState({current_prod: result});
        }
        else {
            this.refs.input_prod.focus();
        }
    },
    loadProdSearch: function(uid, result) {
        this.loadProd(uid, result);
        this.refs.searchProd.hide();
    },
    inputCant: function(event) {
        if (event.key == 'Enter') {
            var cant = Number(this.refs.input_cant.value);
            this.state.items.push({prod: this.state.current_prod, cant: cant});
            this.setState({items: this.state.items, current_prod: null});
            console.log(cant);
            this.refs.input_prod.focus();
            this.refs.input_prod.setValue('');
            this.setState({current_cant: null});
        }
    },
    showSearchProd: function(event) {
        this.refs.searchProd.show();
    },
    saveDoc: function(isOrden) {
        var url= isOrden ? '/api/nota' : '/api/pedido';
        var doc = {meta: computeTotals(this.state.items), items: this.state.items};
        doc.meta.almacen_id = this.state.meta.almacen_id;
        doc.meta.user = this.props.user.username;
        doc.meta.codigo = this.state.codigo;
        doc.meta.tax_percent = IVA_PERCENT;
        doc.meta.bodega_id = this.props.user.bodega_id;
        doc.meta.paid = true;
        doc.meta.paid_amount = this.state.paid_amount;
        doc.meta.payment_format = this.state.payment_format;
        doc.options = {};
        doc.options.usar_decimal = true;
        doc.options.incrementar_codigo = true;

        $.ajax({
            url: url,
            method: 'POST',
            data: JSON.stringify(doc),
            success: function(x) {
                console.log(x);
            }
        });
    },
    render: function() {
        var current_prod_name = '';
        var current_price = '';
        var current_subtotal = '';
        if (this.state.current_prod) {
            var p = this.state.current_prod;
            current_prod_name = p.nombre;
            current_price = p.precio1 / 100;
            current_subtotal = p.precio1 * (this.state.current_cant || 0) / 100;
        }

        var subtotal = 0;

        for (var x in this.state.items) {
            var x = this.state.items[x];
            subtotal += (x.cant * x.prod.precio1);
        }
        var iva = Math.round(IVA_PERCENT * subtotal / 100 );
        var total = subtotal + iva;
        return <div className="container full">
            <SkyLight dialogStyles={searchStyles} hiddenOnOverlayClicked 
                      ref="searchProd" title="Buscar Producto"
                      afterOpen={() => {this.refs.searchProdBox.focus()}}>

                <Searcher ref='searchProdBox' url={'/api/alm/' + this.state.meta.almacen_id + '/producto?prefijo='} 
                          display={(x) => x.nombre} onSelectItem={this.loadProdSearch}/>
            </SkyLight>
            <SkyLight dialogStyles={searchStyles} hiddenOnOverlayClicked 
                      ref="searchClient" title="Buscar Cliente"
                      afterOpen={() => {this.refs.searchClientBox.focus()}}>
                <Searcher ref='searchClientBox' url='/api/cliente?prefijo='
                          display={(x) => x.apellidos + ' ' + (x.nombres || '')} 
                          onSelectItem={this.loadClientSearch}/>
            </SkyLight>
            <div className="row">
                <h3>Usuario: {this.props.user.username} </h3>
                <div className="col-md-12">
                    <input ref="pedido_id" />
                    <button className="btn btn-sm btn-success" 
                        onClick={this.loadPedido} >Cargar Pedido</button>
                    <button className="btn btn-sm btn-primary" 
                        onClick={this.loadOrden} >Cargar Orden de Despacho</button>
                    <button className="btn btn-sm btn-warning" 
                        onClick={this.saveDoc.bind(this, false)} >Guardar Como Pedido</button>
                    <button className="btn btn-sm btn-danger" 
                        onClick={this.saveDoc.bind(this, true)} >Guardar Como Orden</button>

                </div>
            </div>
            <div className="row">
                <div className="col-md-12">
                <button className="btn btn-sm btn-primary" onClick={()=>this.refs.searchClient.show()}>Buscar</button>
                Cliente: <ItemLoader ref='input_client' handleItem={this.loadClient}
                    url="/api/cliente/" />
                    <span>
                    {
                        this.state.client ? 
                        this.state.client.apellidos  + ' ' + (this.state.client.nombre || ''): ''
                    }
                    </span>
                </div>
                <div className="col-md-12">
                <button className="btn btn-sm btn-success" 
                   onClick={this.showSearchProd}>Buscar</button>Producto: 
                   <ItemLoader size="10" handleItem={this.loadProd} ref="input_prod"
                    url="/api/alm/1/producto/"/>
                <input valueLink={this.linkState('current_cant')} 
                       size="10" ref="input_cant" placeholder="CANTIDAD" onKeyDown={this.inputCant} />
                <span style={{width:"50%"}}> {current_prod_name}</span>
                <span className="value_col" style={{width:"10%"}}> {current_price}</span>
                <span className="value_col" style={{width:"10%"}}>{current_subtotal}</span>
                </div>
            </div>
            <div className="row" style={{height:"70%"}}>
                <div className="col-md-12 full scroll-area">
                <ItemAndCant items={this.state.items} />
                </div>
            </div>
            <div className="row">
                <div className="col-md-12">
                Subtotal: {subtotal/100} IVA: {iva/100} Total: {total/100}
                </div>
            </div>
        </div>;
    }
});

export var InvForm = React.createClass({
    getInitialState: function() {
        return {user: null};
    },
    render: function() {
        return this.state.user ? <InvFormContent user={this.state.user} /> :
                       <LoginForm callback={(x) => this.setState({user: x})} />;
    }
});


// core object
// meta e items
// index de prod_id -> item number
