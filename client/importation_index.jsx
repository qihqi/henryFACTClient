import ReactDOM from 'react-dom';
import React from 'react';
import {Route, Router, Link, browserHistory} from 'react-router';
import {CreateInvBox, ShowProd, ShowPurchase, PurchaseContent} from './importation';

var router = <Router history={browserHistory}>
    <Route name="createpurchase" path='/createpurchase' component={CreateInvBox} />
    <Route name="allprod" path='/allprod' component={ShowProd} />
    <Route name="allpurchase" path='/allpurchase' component={ShowPurchase} />
    <Route name="purchase" path='/purchase/:uid' component={PurchaseContent} />
</Router>;
ReactDOM.render(router, document.getElementById("content"));

