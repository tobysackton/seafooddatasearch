import Papa from 'papaparse';

export const loadCsvData = async (filePath) => {
  try {
    const response = await fetch(filePath);
    const csvText = await response.text();
    
    return new Promise((resolve) => {
      Papa.parse(csvText, {
        header: true,
        dynamicTyping: true,
        complete: (results) => {
          resolve(results.data);
        }
      });
    });
  } catch (error) {
    console.error('Error loading CSV:', error);
    return [];
  }
};