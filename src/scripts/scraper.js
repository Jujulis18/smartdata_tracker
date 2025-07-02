#!/usr/bin/env node

const { chromium } = require("playwright");
const fs = require("fs");


const CONFIG = {
  url: "https://www.therapixel.fr/blog/",
  locatorTitle: "h3 > a",
  locatorDescription: ".entry-content > p",
  locatorDate: ".entry-date",
  locatorLink: ".entry-image > a",
  locatorNextPage: ".pagination .page-next",
  category: "medical"
};

const generateCSV = (articles) => {
  const headers = 'Title,Description,Link,Date,Category\n';
  const rows = articles.map(article => {
    const escape = (str) => {
      if (!str) return '';
      str = str.toString().replace(/"/g, '""');
      return /[",\n]/.test(str) ? `"${str}"` : str;
    };
    return [
      escape(article.title),
      escape(article.description),
      escape(article.link),
      escape(article.date),
      escape(article.category)
    ].join(',');
  });
  return headers + rows.join('\n');
};

const extractArticlesFromPage = async (page, config) => {
  const titles = await page.locator(config.locatorTitle).elementHandles();
  const descriptions = await page.locator(config.locatorDescription).allTextContents();
  const dates = await page.locator(config.locatorDate).allTextContents();

  const articles = [];
  for (let i = 0; i < titles.length; i++) {
    const title = await titles[i].textContent() || '';
    const href = await titles[i].getAttribute('href') || '';
    const link = href.startsWith('http') ? href : new URL(href, CONFIG.url).href;
    const description = descriptions[i] || '';
    const date = dates[i] || '';

    if (title.trim()) {
      console.log("Title:", title);
      articles.push({
        title: title.trim(),
        description: description.trim(),
        link,
        date: date.trim(),
        category: config.category
      });
    }
  }

  return articles;
};

const clickNextPage = async (page, selector, previousFirstTitle, previousUrl) => {
  const nextBtn = page.locator(selector);
  if (!(await nextBtn.count())) return false;

  const isVisible = await nextBtn.isVisible();
  const isEnabled = await nextBtn.isEnabled();

  if (isVisible && isEnabled) {
    await nextBtn.click();

    try {
      // 1) Attendre le changement d'URL (court timeout)
      await page.waitForFunction(
        oldUrl => window.location.href !== oldUrl,
        previousUrl,
        { timeout: 2000 }
      );

      // Si on arrive ici, l'URL a changé, on return true
      return true;

    } catch {
      // L'URL n'a pas changé après 2s, on attend alors un changement du titre (plus long timeout)
      try {
        await page.waitForFunction(
          (selector, oldTitle) => {
            const el = document.querySelector(selector);
            const newTitle = el ? el.textContent.trim() : null;
            return newTitle && newTitle !== oldTitle;
          },
          selector,
          previousFirstTitle,
          { timeout: 500 }
        );

        return true;
      } catch {
        console.log("⏳ Aucun changement détecté après le clic. Fin du scraping.");
        return false;
      }
    }
  }


  return false;
};




const startScrapingProcess = async ({ onProgress } = {}) => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(CONFIG.url);

  let currentPage = 1;
  const allArticles = [];

  try {
    let hasMore = true;

    let previousFirstTitle = "";

    let previousUrl = page.url();

    while (hasMore) {
      console.log(`→ Scraping de la page ${currentPage}`);
      await page.waitForSelector(CONFIG.locatorTitle);

      const articles = await extractArticlesFromPage(page, CONFIG);
      console.log(`✓ ${articles.length} articles trouvés`);
      allArticles.push(...articles);

      // Stocke le titre principal
      previousFirstTitle = articles[0]?.title || "";

      if (articles.length > 0) {
        previousFirstTitle = articles[0].title;
      }
      previousUrl = page.url();

      hasMore = await clickNextPage(page, CONFIG.locatorNextPage, previousFirstTitle, previousUrl);

      if (hasMore) {
        currentPage++;
        await page.waitForTimeout(5000); // facultatif si waitForFunction est suffisant
      } else {
        console.log("→ Fin des pages");
      }
    }

  } catch (error) {
    console.error("❌ Erreur pendant le scraping:", error);
  } finally {
    await browser.close();
  }

  console.log(`✓ Scraping terminé : ${allArticles.length} articles sur ${currentPage} pages`);
  const csvData = generateCSV(allArticles);
  return {
    articles: allArticles,
    csvData,
    totalPages: currentPage,
    totalArticles: allArticles.length
  };
};

const runScraper = async () => {
  const result = await startScrapingProcess({
    onProgress: ({ currentPage, totalArticles }) => {
      console.log(`... Page ${currentPage} terminée, ${totalArticles} articles au total`);
    }
  });

  console.log("🎉 Scraping terminé !");
  console.log("Articles:", result.totalArticles);
  console.log("Pages:", result.totalPages);
  // fs.writeFileSync('articles.csv', result.csvData); // à activer si besoin
  return result;
};

module.exports = { startScrapingProcess };

// Décommenter pour exécuter
if (require.main === module) {
  runScraper();
}