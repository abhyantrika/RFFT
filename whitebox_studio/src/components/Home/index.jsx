import React from 'react';
import constants from '../../constants';
import './Home.css';
class ExperimentCard extends React.Component {
  getDomainName = (domainId) => {
    switch(domainId) {
      case 0:
        return 'Text';
      case 1:
        return 'Image';
      case 2:
        return 'Tabular';
      default:
        return 'Other';
    }
  }

  render() {
    const {
      name, description, domain, started,
    } = this.props.experiment;
    return (
      <div className="Home-ExperimentCard">
        <div className="Home-ExperimentCard-info">
          <h1 className="Home-ExperimentCard-name">{name}</h1>
          <p className="Home-ExperimentCard-desc">{description}</p>
          <h2 className="Home-ExperimentCard-domain">{this.getDomainName(domain)}</h2>
        </div>
        <button className="Home-ExperimentCard-button" onClick={this.props.goToWorkspace}>{started ? 'Resume experiment' : 'Start experiment'}</button>
      </div>
    );
  }
}


class PreTrainedExperimentCard extends React.Component {
render() {
    const {
      name, per_annotation, num_epochs, n_annotations, hypothesis_weight, test_accuracy, train_accuracy,
    } = this.props.experiment;
    return (
      <div className="Home-PreExperimentCard">
        <div className="Home-ExperimentCard-info">
          <h1 className="Home-ExperimentCard-name">{name}</h1>

          <div className="Home-ExperimentCard-params">
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`num of epochs`}</p>
            <p className="Home-ExperimentCard-desc">{`${num_epochs}`}</p>
            </div>
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`annotations used`}</p>
            <p className="Home-ExperimentCard-desc">{` ${per_annotation}`}</p>
            </div>
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`number of annotations`}</p>
            <p className="Home-ExperimentCard-desc">{`${n_annotations}`}</p>
            </div>
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`hypothesis weight`}</p>
            <p className="Home-ExperimentCard-desc">{`${hypothesis_weight}`}</p>
            </div>
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`test accuracy`}</p>
            <p className="Home-ExperimentCard-desc">{`${test_accuracy}%`}</p>
            </div>
            <div className="Home-ExperimentCard-paramField">
            <p className="Home-ExperimentCard-desc">{`training accuracy`}</p>
            <p className="Home-ExperimentCard-desc">{` ${train_accuracy}%`}</p>
            </div>
          </div>
        </div>
        <button className="Home-ExperimentCard-button" onClick={this.props.goToExplain}>Explain</button>
      </div>
    );
  }
}
class ExperimentList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      all_experiments: [],
      pre_trained_expereiments: [],
    };
  }

  componentDidMount = () => {
    const API = `${constants.API}/all_experiments`;
    const API2 = `${constants.API}/saved_experiments/`;
    fetch(API)
      .then(response => response.json())
      .then(data => {
        console.log(data);
        this.setState({ all_experiments: data.all_experiments });
        // data.all_experiments.forEach(experiment => {
        //   fetch(`${API2}${experiment.id}`)
        //   .then(response2 => response2.json())
        //   .then(data2 => {
        //     this.setState({ saved_experiments: data2.saved_experiments });
        //   });
        // });
      });

      
        fetch(`${API2}DecoyMNIST`)
        .then(response2 => response2.json())
        .then(data2 => {
          console.log(data2);
          this.setState({ pre_trained_expereiments: data2 });
        });
  }

  goToWorkspace = (experiment) => () => {
    this.props.goToWorkspace(experiment);
  }

  goToExplain = (experiment) => () => {
    this.props.goToExplain(experiment);
  }

  renderCards = () => this.state.all_experiments.map(experiment => (
    <ExperimentCard key={experiment.id} experiment={experiment} goToWorkspace={this.goToWorkspace(experiment)}/>
  ))

  renderPreCards = () => this.state.pre_trained_expereiments.map(experiment => (
    <PreTrainedExperimentCard key={experiment.id} experiment={experiment} goToExplain={this.goToExplain(experiment)}/>
  ))

  render() {
    return (
      <div className="Home">
      <div className="experimentList">
        {this.renderCards()}
      </div>
      <div className="experimentList">
        {this.renderPreCards()}
      </div>
      </div>
    );
  }
}

class Home extends React.Component {
  render() {
    return (
      <div className="Home">
        <ExperimentList goToWorkspace={this.props.goToWorkspace} goToExplain={this.props.goToExplain}/>
      </div>
    );
  }
}

export default Home;
