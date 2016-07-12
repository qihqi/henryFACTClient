import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';
import {Bar, Line} from 'react-chartjs';
import {EditPurchase} from './importation_purchase';

const API = '/import';

var FIX_HEADER = {position: 'fixed', top: '0', width:'100%', zIndex: 10, backgroundColor: 'white'};
var RAINBOW_COLOR = ['red','magenta', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'pink'];

// http://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript-jquery
function hashCode(s){
  return s.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0);
}

export class CustomFull extends React.Component {
    constructor(props) {
        super(props)
        this.getCustom(this.props.params.uid);
        this.setItemValue = this.setItemValue.bind(this);
        this.saveCustom = this.saveCustom.bind(this);
        this.splitCustom = this.splitCustom.bind(this);
        this.openPList = () => window.open(API + '/custom_plist/' + props.params.uid);
        this.openInvoice= () => window.open(API + '/custom_invoice/' + props.params.uid);
        this.state = {
            meta: {},
            customs: [],
            units: {},
        }
    }
    getCustom(uid) {
        $.ajax({
            url: API + '/custom_full/' + uid,
            success: (x) => {
                x = JSON.parse(x);
                this.setState(x);
            }
        });
    }
    splitCustom(index) {
        var item = this.state.customs[index];
        $.ajax({
            url: API + '/split_custom_items',
            data: JSON.stringify(item),
            method: 'POST',
            success: (x) => {
                x = JSON.parse(x);
                this.state.customs.splice(index, 1);
                for (var i in x.result) {
                    this.state.customs.splice(index, 0, x.result[i]);
                }
                this.setState({customs: this.state.customs});
            }
        });
    }
    saveCustom() {
        var modifiedRows = [];
        for (var i in this.state.customs) {
            var cust = this.state.customs[i];
            if (cust.custom._edited || ('grouping' in cust.custom && cust.custom.grouping > 0)) {
                modifiedRows.push(cust);
            }
        }
        console.log('modifed', modifiedRows);
        $.ajax({
            url: API + '/custom_full/' + this.props.params.uid,
            method: 'PUT',
            data: JSON.stringify({customs: modifiedRows}),
            success: (x) => {
                this.getCustom(this.props.params.uid);
            }
        });
    }
    setItemValue(index, name, value) {
        console.log(name, value);
        this.state.customs[index].custom[name] = value;
        if (name != 'grouping') {
            this.state.customs[index].custom._edited = true;
        }
    //    this.setState({customs: this.state.customs});
    }
    render() {
        console.log('render container');
        return (<div className="container">
            <div style={FIX_HEADER}>
                <h3>Contenedor #{this.props.params.uid}</h3>
                <button onClick={this.saveCustom}>Guardar</button>
                <button onClick={this.openInvoice}>Imprimir Invoice</button>
                <button onClick={this.openPList}>Imprimir Packing List</button>
            </div>
            <div className="row" style={{marginTop: "100px"}}>
                <div className="col-xs-1">Agrupar?</div>
                <div className="col-xs-1">Cod</div>
                <div className="col-xs-3">Producto</div>
                <div className="col-xs-1">Cantidad</div>
                <div className="col-xs-2">Unidad</div>
                <div className="col-xs-1">Precio</div>
                <div className='smallNum col-xs-1'>Total</div>
                <div className="col-xs-1">Cartones</div>
                <div className="col-xs-1">Detalle</div>
           </div>
           <div ref='allChildren'>
            {this.state.customs.map((x, index) => {
                return <SingleCustomRow
                        key={`${x.custom.uid}-${x.purchase_items.length}-${hashCode(JSON.stringify(x.custom))}`}
                        {...x.custom} index={index}
                        setItemValue={this.setItemValue} purchase_items={x.purchase_items}
                        units={this.state.units} 
                        splitCustom={this.splitCustom} />;
            })}
           </div>
        </div>);
    }
}

class SingleCustomRow extends React.Component {
    constructor(props) {
        super(props)
        this.onChange = this.onChange.bind(this);
        this.splitCustom = this.splitCustom.bind(this);
        this.state = Object.assign({}, props);
    }
    onChange(event) {
        var name = event.target.name;
        var value = event.target.value;
        this.props.setItemValue(this.props.index, name, value);
        var newState = {};
        newState[name] = value;
        if (name != 'grouping') {
            newState['_edited'] = true;
        }
        this.setState(newState);
    }
    splitCustom() {
        this.props.splitCustom(this.props.index);
    }
    render() {
        var moreStyle = {marginTop: '5px', border:'1px solid grey'};
        var edited = '_edited' in this.state && this.state._edited;
        if (edited) {
            moreStyle['font-weight'] = 'bold';
        }
        if ('grouping' in this.state && this.state.grouping > 0) {
            var color = (this.state.grouping - 1) % RAINBOW_COLOR.length;
            color = RAINBOW_COLOR[color];
            moreStyle['background-color'] = color;
        }
        return <div style={moreStyle}>
            <div className="row">
            <div className="col-xs-1 smallpadding">
                <input className="value_col tableCell" name='grouping'
                    style={{width:'80%', 'float': 'right'}} value={this.state.grouping}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className="value_col tableCell" name='box_code' value={this.state.box_code}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-3 smallpadding">
                <input name='display_name' className="tableCell" value={this.state.display_name}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className=" value_col tableCell" name='quantity' value={Number(this.state.quantity)}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-2 smallpadding">
                <input name='unit' className="tableCell" value={this.state.unit}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className=" value_col tableCell" name='price_rmb'
                       value={Number(this.state.price_rmb).toFixed(2)}
                       onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding value_col">
                {(this.state.price_rmb * this.state.quantity).toFixed(2)}</div>
            <div className="col-xs-1">
                <input className="value_col tableCell" name='box' value={this.state.box}
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <button className="btn btn-primary btn-xs" data-toggle='collapse'
                    data-target={'#purchase' + this.props.uid}>Ver</button>

                { this.props.purchase_items.length > 1 ?
                <button onClick={this.splitCustom} 
                        className="btn btn-danger btn-xs">Separar</button> : ''}
            </div>
            </div>
            <div className='collapse' id={"purchase" + this.props.uid}>
                {this.props.purchase_items.map((x) => <PurchaseItemRow {...x} units={this.props.units}/>)}
            </div>
        </div>;
    }
}

class PurchaseItemRow extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        var it = this.props;
        var unit = this.props.units[it.prod_detail.unit] ?
            this.props.units[it.prod_detail.unit].name_es : it.prop_detail.unit;
        return <div className="row">
            <div className="col-xs-1 smallpadding"></div>
            <div className="col-xs-1 smallpadding"></div>
            <div className="col-xs-3 smallpadding">{it.prod_detail.name_es}</div>
            <div className="col-xs-1 smallpadding value_col">{Number(it.item.quantity)}</div>
            <div className="col-xs-2 smallpadding">{unit}</div>
            <div className="col-xs-1 smallpadding value_col">{Number(it.item.price_rmb).toFixed(2)}</div>
            <div className='value_col col-xs-1 smallpadding'>{(it.item.price_rmb * it.item.quantity).toFixed(2)}</div>
            <div className="col-xs-1 smallpadding value_col">{it.item.box}</div>
            <div></div>
        </div>;
    }
}
