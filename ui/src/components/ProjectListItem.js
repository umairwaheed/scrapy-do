//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { Button, Glyphicon, Panel } from 'react-bootstrap';
import Dialog from 'react-bootstrap-dialog';

import { BACKEND_OPENED } from '../actions/backend';
import { projectRemove } from '../utils/backendActions';

import ScheduleDialog from './ScheduleDialog';

//------------------------------------------------------------------------------
// Project List Item
//------------------------------------------------------------------------------
class ProjectListItem extends Component {
  //----------------------------------------------------------------------------
  // Property types
  //----------------------------------------------------------------------------
  static propTypes = {
    projectName: PropTypes.string.isRequired
  }

  //----------------------------------------------------------------------------
  // Show remove dialog
  //----------------------------------------------------------------------------
  showRemoveDialog = () => {
    const project = this.props;
    this.dialog.show({
      body: `Are you sure you want to remove project "${project.name}"?`,
      actions: [
        Dialog.CancelAction(),
        Dialog.Action(
          'Remove',
          () => {
            projectRemove(project.name)
              .catch((error) => {
                setTimeout(() => this.dialog.showAlert(error.message), 250);
              });
          },
          'btn-danger'
        )
      ]
    });
  };

  //----------------------------------------------------------------------------
  // Show schedule dialog
  //----------------------------------------------------------------------------
  showScheduleDialog = (project, spider) => {
    this.scheduleDialogCtl.showForSpider(project, spider);
  };

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    const project = this.props;
    return(
      <Panel>
        <Dialog ref={(el) => { this.dialog = el; }} />
        <ScheduleDialog
          provideController={ctl => this.scheduleDialogCtl = ctl}
        />

        <Panel.Heading >
          <div className='list-item'>
            <div className='item-panel'>
              <Button
                bsSize="xsmall"
                disabled={!this.props.connected}
                onClick={this.showRemoveDialog}
              >
                <Glyphicon glyph='trash'/> Remove
              </Button>
            </div>
            <strong>{project.name}</strong>
          </div>
        </Panel.Heading>
        <Panel.Body>
          <div className='spider-list'>
            {project.spiders.map(spider => (
              <Button
                bsSize="xsmall"
                disabled={!this.props.connected}
                key={spider}
                onClick={() => this.showScheduleDialog(project.name, spider)}
              >
                <Glyphicon glyph='flash'/> {spider}
              </Button>
            ))}
          </div>
        </Panel.Body>
      </Panel>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    ...state.projects[ownProps.projectName],
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectListItem);
