import React from 'react';
import constants from '../../constants';
import './Explain.css';

class Explain extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      index: 0,
      uri: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAAAAABXZoBIAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAlwSFlzAAAOwwAADsMBx2+oZAAAAAl2cEFnAAAAHAAAABwAh7EitAAAANBJREFUKM9jYBjMgFlISKiuY73Usv/f61Ek5FTiZq36CwIP1/z9dNgBWc7w3V8o+B0bFGShjqJR6DZY5ti27x+x2BcwJ/vv37PcDNqzsLmGj3HW3yjcju3+u48JpyT3vr9uuLUqf3y4IIcRl2zgh79/yyVxyeru+vt3mjQuWYHYP39347b459+fDthl9Jq2//17HquH1Kc8BQbhr21YpCSK7oKC96QfppS401VwyAdimim0GhwrhwM4MaTM1zwCSX1p5cZiWwdQ5kp7iwADfQAA+21rhoBnKQwAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTgtMDItMTlUMTI6NTg6NDkrMDk6MDAeWgaLAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE4LTAyLTE5VDEyOjU4OjQ5KzA5OjAwbwe+NwAAABd0RVh0cG5nOmJpdC1kZXB0aC13cml0dGVuAAinxCzyAAAAAElFTkSuQmCC',
    };
  }

  getImage = (index) => {
    const API = `${constants.API}/apipath/${index}`;
    fetch(API)
      .then(response => response.json())
      .then(data => {
        this.setState({uri: data.data}); 
      });

  }

  getNextImage = () => {
    this.getImage(this.state.index + 1);
    this.setState({ index: this.state.index + 1 });
  }

  getPreviousImage = () => {
    this.getImage(this.state.index - 1);
    this.setState({ index: this.state.index - 1 });
  }

  render() {
    return (
      <div className="Explain">
        <button onClick={this.getPreviousImage}>previous</button>
        <img alt="" src={this.state.uri} height={280} width={280} />
        <button onClick={this.getNextImage}>next</button>
      </div>
    );
  }
}

export default Explain;
