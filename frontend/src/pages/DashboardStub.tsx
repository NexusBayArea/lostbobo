import React from 'react';

const DashboardStub = () => {
  return React.createElement('div', { 
    style: { 
      padding: '2rem', 
      textAlign: 'center', 
      fontFamily: 'sans-serif',
      color: '#666'
    } 
  }, 'Mission Control is currently unavailable in this environment.');
};

export const Dashboard = DashboardStub;
export default DashboardStub;
