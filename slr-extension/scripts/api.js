const API_BASE_URL = 'http://localhost:8000';

const api = {
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch (e) {
      console.error('API Health Check failed:', e);
      return false;
    }
  },

  async getProjects() {
    // Mock for now until backend endpoint exists
    // return fetch(`${API_BASE_URL}/extension/projects`).then(r => r.json());
    return Promise.resolve([
        { id: 'default', name: 'My First SLR' }
    ]);
  },

  async savePaper(paper, projectId) {
    try {
      const response = await fetch(`${API_BASE_URL}/extension/papers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...paper, project_id: projectId })
      });
      return response.json();
    } catch (e) {
      console.error('Failed to save paper:', e);
      throw e;
    }
  },
  
  async deletePaper(paperId) {
      try {
          const response = await fetch(`${API_BASE_URL}/extension/papers/${paperId}`, {
              method: 'DELETE'
          });
          return response.ok;
      } catch (e) {
          console.error('Failed to delete paper:', e);
          throw e;
      }
  },
  
  async getPapers(projectId) {
      try {
          const response = await fetch(`${API_BASE_URL}/extension/papers?project_id=${projectId}`);
          if (!response.ok) return [];
          return response.json();
      } catch (e) {
          console.error('Failed to get papers:', e);
          return [];
      }
  }
};

// Export for module use if needed, but in standard extension scripts we often just load it globally or use modules
// export default api;
