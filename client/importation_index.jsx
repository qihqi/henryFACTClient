import ReactDOM from 'react-dom';
import React from 'react';
import {Route, Router, Link, browserHistory} from 'react-router';
import {SaleReportByDateFull, InvMovementListFull, CreateInvBox, ShowProd, ShowPurchase, PurchaseContent} from './importation';
import {EditPurchase} from './importation_purchase';


var ShowIndex = React.createClass({
    render: function() {
        return <ul>
            <li><a href="#/createpurchase">Crear Importacion {"创建新进口"}</a></li>
            <li><a href="#/allprod">Productos {"产品"}</a></li>
            <li><a href="#/allpurchase">Importaciones pasados {"进口"}</a></li>
            <li><a href="#/inv_movements">Movimientos {""}</a></li>
            <li><a href="#/sale_report">SaleReport {""}</a></li>
        </ul>;
    }
});

var router = <Router history={browserHistory}>
    <Route name="createpurchase" path='/createpurchase' component={CreateInvBox} />
    <Route name="allprod" path='/allprod' component={ShowProd} />
    <Route name="allpurchase" path='/allpurchase' component={ShowPurchase} />
    <Route name="purchase" path='/purchase/:uid' component={PurchaseContent} />
    <Route name="purchase" path='/inv_movements/:date' component={InvMovementListFull} />
    <Route name="sale_report" path='/sale_report' component={SaleReportByDateFull} />
    <Route name="edit_purchase" path='/edit_purchase/:uid' component={EditPurchase} />
    <Route name="index" path='/' component={ShowIndex} />
</Router>;
ReactDOM.render(router, document.getElementById("content"));

