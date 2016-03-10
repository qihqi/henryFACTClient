module.exports = {
  entry: {
    prod: './client/index.jsx',
    accounting: './client/accounting_index.jsx',
    viewprod : './client/view_prod_index.jsx',
    transfer: './client/prod_components.jsx'
  },
  output: {
    path: __dirname + '/static',
    publicPath: '/static',
    filename: '[name]-bundle.js'
  },
  devServer: {
    contentBase: './dist'
  },
  module: {
    loaders: [{
      test: /\.jsx?$/,
      exclude: /node_modules/,
      loader: 'babel'
    }]
  },
  resolve: {
    extensions: ['', '.js', '.jsx']
  },
};
