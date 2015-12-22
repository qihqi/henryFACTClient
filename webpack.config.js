module.exports = {
  entry: [
    './client/index.jsx'
  ],
  output: {
    path: __dirname + '/static',
    publicPath: '/static',
    filename: 'bundle.js'
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
