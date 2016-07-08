import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';
import {Bar, Line} from 'react-chartjs';
import {EditPurchase} from './importation_purchase';

const API = '/import';

var FIX_HEADER = {position: 'fixed', top: '0', width:'100%', zIndex: 10, backgroundColor: 'white'};
var RAINBOW_COLOR = ['red','magenta', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'pink'];

export class CustomFull extends React.Component {
    constructor(props) {
        super(props)
        this.getCustom(this.props.params.uid);
        this.setItemValue = this.setItemValue.bind(this);
        this.saveCustom = this.saveCustom.bind(this);
        this.state = {
            meta: {},
            customs: [],
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
    saveCustom() {
        $.ajax({
            url: API + '/custom_full/' + this.props.params.uid,
            method: 'PUT',
            data: JSON.stringify(this.state),
            success: (x) => {
                this.getCustom(this.props.params.uid);
                alert('Guardado con exito');
            }
        });
    }
    setItemValue(index, name, value) {
        this.state.customs[index].custom[name] = value;
        if (name != 'grouping') {
            this.state.customs[index].custom._edited = true;
        }
        this.setState({customs: this.state.customs});
    }
    render() {
        return (<div className="container">
            <div style={FIX_HEADER}>
                <h3>Contenedor #{this.props.params.uid}</h3>
                <button onClick={this.saveCustom}>Guardar</button>
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
            {this.state.customs.map((x, index) => {
                return <SingleCustomRow {...x.custom} index={index} 
                        setItemValue={this.setItemValue} purchase_items={x.purchase_items}/>;
            })}
        </div>);
    }
}

class SingleCustomRow extends React.Component {
    constructor(props) {
        super(props)
        this.onChange = this.onChange.bind(this);
    }
    onChange(event) {
        var name = event.target.name;
        var value = event.target.value;
        this.props.setItemValue(this.props.index, name, value);
    }
    render() {
        var moreStyle = {marginTop: '5px', border:'1px solid grey'};
        var edited = '_edited' in this.props && this.props._edited;
        if (edited) {
            moreStyle['font-weight'] = 'bold';
        }
        if ('grouping' in this.props) {
            var color = this.props.grouping % RAINBOW_COLOR.length;
            color = RAINBOW_COLOR[color];
            moreStyle['background-color'] = color;
        }
        return <div style={moreStyle}>
            <div className="row">
            <div className="col-xs-1 smallpadding">
                <input className="value_col tableCell" name='grouping' 
                    style={{width:'80%', 'float': 'right'}} value={this.props.grouping} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className="value_col tableCell" name='box_code' value={this.props.box_code} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-3 smallpadding">
                <input name='display_name' className="tableCell" value={this.props.display_name} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className=" value_col tableCell" name='quantity' value={Number(this.props.quantity)} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-2 smallpadding">
                <input name='unit' className="tableCell" value={this.props.unit} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding">
                <input className=" value_col tableCell" name='price_rmb' 
                       value={Number(this.props.price_rmb).toFixed(2)} 
                       onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding value_col">
                {(this.props.price_rmb * this.props.quantity).toFixed(2)}</div>
            <div className="col-xs-1">
                <input className="value_col tableCell" name='box' value={this.props.box} 
                    onChange={this.onChange} />
            </div>
            <div className="col-xs-1 smallpadding" data-toggle='collapse' 
                data-target={'#purchase' + this.props.uid} >
                <button className="btn btn-primary btn-xs">Ver</button>
            </div>
            </div>
            <div className='collapse' id={"purchase" + this.props.uid}>
                {this.props.purchase_items.map((x) => <PurchaseItemRow {...x} />)}
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
        return <div className="row">
            <div className="col-xs-1 smallpadding"></div>
            <div className="col-xs-1 smallpadding"></div>
            <div className="col-xs-3 smallpadding">{it.prod_detail.name_es}</div>
            <div className="col-xs-1 smallpadding value_col">{Number(it.item.quantity)}</div>
            <div className="col-xs-2 smallpadding">{it.prod_detail.unit}</div>
            <div className="col-xs-1 smallpadding value_col">{Number(it.item.price_rmb).toFixed(2)}</div>
            <div className='value_col col-xs-1 smallpadding'>{(it.item.price_rmb * it.item.quantity).toFixed(2)}</div>
            <div className="col-xs-1 smallpadding value_col">{it.item.box}</div>
            <div></div>
        </div>;
    }
}
