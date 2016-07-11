import ReactDOM from 'react-dom';
import React from 'react';
import {Route, Router, Link, browserHistory} from 'react-router';
import {SaleReportByDateFull, InvMovementListFull, CreateInvBox, ShowProd, ShowDeclared, ShowPurchase, ShowPurchase2, PurchaseContent} from './importation';
import {EditPurchase} from './importation_purchase';
import {CustomFull} from './importation_custom';


var ShowIndex = React.createClass({
    render: function() {
        return <ul>
            <li><a href="#/allpurchase">Ver Compras</a></li>
        </ul>;
    }
});

var router = <Router history={browserHistory}>
    <Route name="createpurchase" path='/createpurchase' component={CreateInvBox} />
    <Route name="allprod" path='/allprod' component={ShowProd} />
    <Route name="alldeclared" path='/alldeclared' component={ShowDeclared} />
    <Route name="allpurchase" path='/allpurchase' component={ShowPurchase} />
    <Route name="kanhuogui" path='/kanhuogui' component={ShowPurchase2} />
    <Route name="purchase" path='/purchase/:uid' component={PurchaseContent} />
    <Route name="purchase" path='/inv_movements/:date' component={InvMovementListFull} />
    <Route name="sale_report" path='/sale_report' component={SaleReportByDateFull} />
    <Route name="edit_purchase" path='/edit_purchase/:uid' component={EditPurchase} />
    <Route name="edit_custom" path='/edit_custom/:uid' component={CustomFull} />
    <Route name="index" path='/' component={ShowIndex} />
</Router>;
ReactDOM.render(router, document.getElementById("content"));

