module.exports = {
  entry: {
    prod: './client/index.jsx',
    accounting: './client/accounting_index.jsx',
    transfer: './client/prod_components.jsx',
    importation: './client/importation_index.jsx',
    create_inv: './client/create_inv_index.jsx'
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
      loader: 'babel-loader',
      presets: ['es2015', 'react']
    }]
  },
  resolve: {
    extensions: ['', '.js', '.jsx']
  },
};
