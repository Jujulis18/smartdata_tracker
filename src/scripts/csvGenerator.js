// scripts/csvGenerator.js

export const generateCSV = (articles) => {
  const headers = ['numero', 'titre', 'lien', 'extrait', 'page_trouvee'];
  const escapeCSVField = (field) => {
    if (field === null || field === undefined) return '';
    const stringField = String(field);
    return (stringField.includes('"') || stringField.includes(',') || stringField.includes('\n'))
      ? `"${stringField.replace(/"/g, '""')}"`
      : stringField;
  };

  return [
    headers.join(','),
    ...articles.map((a, i) => [
      i + 1,
      escapeCSVField(a.title),
      escapeCSVField(a.link),
      escapeCSVField(a.excerpt),
      a.page
    ].join(','))
  ].join('\n');
};

export const generateFileName = () => {
  return `kommunicate_healthcare_articles_${new Date().toISOString().slice(0, 10)}.csv`;
};

export const downloadCSV = (csvData, articleCount = 0) => {
  try {
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', generateFileName());
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    console.log(`✅ Téléchargement CSV : ${articleCount} articles`);
  } catch (error) {
    console.error('❌ Erreur CSV:', error);
  }
};

export const previewCSV = (csvData, maxLines = 5) => {
  const lines = csvData.split('\n');
  return lines.slice(0, maxLines).join('\n');
};
