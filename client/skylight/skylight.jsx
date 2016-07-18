import React from 'react';
import SkylightStateless from './skylightstateless';

const isOpening = (s1, s2) => !s1.isVisible && s2.isVisible;
const isClosing = (s1, s2) => s1.isVisible && !s2.isVisible;

export default class SkyLight extends React.Component {

  constructor(props) {
    super(props);
    this.state = { isVisible: false };
  }

  componentWillUpdate(nextProps, nextState) {
    if (isOpening(this.state, nextState) && this.props.beforeOpen) {
      this.props.beforeOpen();
    }

    if (isClosing(this.state, nextState) && this.props.beforeClose) {
      this.props.beforeClose();
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (isOpening(prevState, this.state) && this.props.afterOpen) {
      this.props.afterOpen();
    }

    if (isClosing(prevState, this.state) && this.props.afterClose) {
      this.props.afterClose();
    }
  }

  show() {
    this.setState({ isVisible: true });
  }

  hide() {
    this.setState({ isVisible: false });
  }

  _onOverlayClicked() {
    if (this.props.hideOnOverlayClicked) {
      this.hide();
    }

    if (this.props.onOverlayClicked) {
      this.props.onOverlayClicked();
    }
  }

  render() {
    return (<SkylightStateless
      {...this.props}
      isVisible={this.state.isVisible}
      onOverlayClicked={() => this._onOverlayClicked()}
      onCloseClicked={() => this.hide()}
    />);
  }
}

SkyLight.displayName = 'SkyLight';

SkyLight.propTypes = Object.assign({}, SkylightStateless.sharedPropTypes);

Object.assign(SkyLight.propTypes, {
  afterClose: React.PropTypes.func,
  afterOpen: React.PropTypes.func,
  beforeClose: React.PropTypes.func,
  beforeOpen: React.PropTypes.func,
  hideOnOverlayClicked: React.PropTypes.bool,
});

SkyLight.defaultProps = Object.assign({}, SkylightStateless.defaultProps);
Object.assign(SkyLight.defaultProps, {
  hideOnOverlayClicked: false,
});
