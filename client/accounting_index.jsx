import ViewAccount from './view_account';
import {Summary} from './summary';
import ReactDOM from 'react-dom';
import React from 'react';

import {Route, Router, Link, browserHistory} from 'react-router'

var router = <Router history={browserHistory}>
    <Route path='/' component={ViewAccount} />
    <Route path='/summary' component={Summary} />
</Router>

ReactDOM.render(router, document.getElementById('content'));
