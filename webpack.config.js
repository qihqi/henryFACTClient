module.exports = {
  entry: {
    prod: './client/index.jsx',
    accounting: './client/accounting_index.jsx',
    viewprod : './client/view_prod_index.jsx'
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
