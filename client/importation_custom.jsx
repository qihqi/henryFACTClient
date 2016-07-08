import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';
import {Bar, Line} from 'react-chartjs';
import {EditPurchase} from './importation_purchase';

const API = '/import';

export class CustomFull extends React.Component {
    constructor(props) {
        super(props)
        this.getCustom(this.props.params.uid);
        this.setItemValue = this.setItemValue.bind(this);
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
    setItemValue(index, name, value) {
        this.state.customs[index].custom[name] = value;
        this.state.customs[index].custom._edited = true;
        this.setState({customs: this.state.customs});
    }
    render() {
        return (<div className="container">
                <div className="row" >
                <div className="col-md-12">
                <table className="table" >
                {this.state.customs.map((x, index) => {
                    return <SingleRow {...x.custom} index={index} 
                                      setItemValue={this.setItemValue} />;
                })}
                </table>
                </div>
                </div>
                </div>);
    }
}

class SingleRow extends React.Component {
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
        var moreStyle = {};
        if ('_edited' in this.props && this.props._edited) {
            moreStyle['background-color'] = 'yellow';
        }
        return <tr style={moreStyle}>
            <td><input name='box_code' value={this.props.box_code} 
                onChange={this.onChange} /></td>
            <td><input name='display_name' value={this.props.display_name} 
                onChange={this.onChange} /></td>
            <td><input className=" smallNum" name='quantity' value={this.props.quantity} 
                onChange={this.onChange} /></td>
            <td><input name='unit' value={this.props.unit} 
                onChange={this.onChange} /></td>
            <td><input className=" smallNum" name='price_rmb' value={this.props.price_rmb} 
                onChange={this.onChange} /></td>
            <td>{(this.props.price_rmb * this.props.quantity).toFixed(2)}</td>
            <td><input className="smallNum" name='box' value={this.props.box} 
                onChange={this.onChange} /></td>
        </tr>;
    }
}
