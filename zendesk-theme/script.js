document.addEventListener('DOMContentLoaded', function() {
  function closest (element, selector) {
    if (Element.prototype.closest) {
      return element.closest(selector);
    }
    do {
      if (Element.prototype.matches && element.matches(selector)
        || Element.prototype.msMatchesSelector && element.msMatchesSelector(selector)
        || Element.prototype.webkitMatchesSelector && element.webkitMatchesSelector(selector)) {
        return element;
      }
      element = element.parentElement || element.parentNode;
    } while (element !== null && element.nodeType === 1);
    return null;
  }

  // social share popups
  Array.prototype.forEach.call(document.querySelectorAll('.share a'), function(anchor) {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      window.open(this.href, '', 'height = 500, width = 500');
    });
  });

  // In some cases we should preserve focus after page reload
  function saveFocus() {
    var activeElementId = document.activeElement.getAttribute("id");
    sessionStorage.setItem('returnFocusTo', '#' + activeElementId);
  }
  var returnFocusTo = sessionStorage.getItem('returnFocusTo');
  if (returnFocusTo) {
    sessionStorage.removeItem('returnFocusTo');
    var returnFocusToEl = document.querySelector(returnFocusTo);
    returnFocusToEl && returnFocusToEl.focus && returnFocusToEl.focus();
  }

  // show form controls when the textarea receives focus or backbutton is used and value exists
  var commentContainerTextarea = document.querySelector('.comment-container textarea'),
    commentContainerFormControls = document.querySelector('.comment-form-controls, .comment-ccs');

  if (commentContainerTextarea) {
    commentContainerTextarea.addEventListener('focus', function focusCommentContainerTextarea() {
      commentContainerFormControls.style.display = 'block';
      commentContainerTextarea.removeEventListener('focus', focusCommentContainerTextarea);
    });

    if (commentContainerTextarea.value !== '') {
      commentContainerFormControls.style.display = 'block';
    }
  }

  // Expand Request comment form when Add to conversation is clicked
  var showRequestCommentContainerTrigger = document.querySelector('.request-container .comment-container .comment-show-container'),
    requestCommentFields = document.querySelectorAll('.request-container .comment-container .comment-fields'),
    requestCommentSubmit = document.querySelector('.request-container .comment-container .request-submit-comment');

  if (showRequestCommentContainerTrigger) {
    showRequestCommentContainerTrigger.addEventListener('click', function() {
      showRequestCommentContainerTrigger.style.display = 'none';
      Array.prototype.forEach.call(requestCommentFields, function(e) { e.style.display = 'block'; });
      requestCommentSubmit.style.display = 'inline-block';

      if (commentContainerTextarea) {
        commentContainerTextarea.focus();
      }
    });
  }

  // Mark as solved button
  var requestMarkAsSolvedButton = document.querySelector('.request-container .mark-as-solved:not([data-disabled])'),
    requestMarkAsSolvedCheckbox = document.querySelector('.request-container .comment-container input[type=checkbox]'),
    requestCommentSubmitButton = document.querySelector('.request-container .comment-container input[type=submit]');

  if (requestMarkAsSolvedButton) {
    requestMarkAsSolvedButton.addEventListener('click', function () {
      requestMarkAsSolvedCheckbox.setAttribute('checked', true);
      requestCommentSubmitButton.disabled = true;
      this.setAttribute('data-disabled', true);
      // Element.closest is not supported in IE11
      closest(this, 'form').submit();
    });
  }

  // Change Mark as solved text according to whether comment is filled
  var requestCommentTextarea = document.querySelector('.request-container .comment-container textarea');

  if (requestCommentTextarea) {
    requestCommentTextarea.addEventListener('input', function() {
      if (requestCommentTextarea.value === '') {
        if (requestMarkAsSolvedButton) {
          requestMarkAsSolvedButton.innerText = requestMarkAsSolvedButton.getAttribute('data-solve-translation');
        }
        requestCommentSubmitButton.disabled = true;
      } else {
        if (requestMarkAsSolvedButton) {
          requestMarkAsSolvedButton.innerText = requestMarkAsSolvedButton.getAttribute('data-solve-and-submit-translation');
        }
        requestCommentSubmitButton.disabled = false;
      }
    });
  }

  // Disable submit button if textarea is empty
  if (requestCommentTextarea && requestCommentTextarea.value === '') {
    requestCommentSubmitButton.disabled = true;
  }

  // Submit requests filter form on status or organization change in the request list page
  Array.prototype.forEach.call(document.querySelectorAll('#request-status-select, #request-organization-select'), function(el) {
    el.addEventListener('change', function(e) {
      e.stopPropagation();
      saveFocus();
      closest(this, 'form').submit();
    });
  });

  // Submit requests filter form on search in the request list page
  var quickSearch = document.querySelector('#quick-search');
  quickSearch && quickSearch.addEventListener('keyup', function(e) {
    if (e.keyCode === 13) { // Enter key
      e.stopPropagation();
      saveFocus();
      closest(this, 'form').submit();
    }
  });

  function toggleNavigation(toggle, menu) {
    var isExpanded = menu.getAttribute('aria-expanded') === 'true';
    menu.setAttribute('aria-expanded', !isExpanded);
    toggle.setAttribute('aria-expanded', !isExpanded);
  }

  function closeNavigation(toggle, menu) {
    menu.setAttribute('aria-expanded', false);
    toggle.setAttribute('aria-expanded', false);
    toggle.focus();
  }

  var burgerMenu = document.querySelector('.header .menu-button');
  var userMenu = document.querySelector('#user-nav');

  // burgerMenu.addEventListener('click', function(e) {
  //   e.stopPropagation();
  //   toggleNavigation(this, userMenu);
  // });


  // userMenu.addEventListener('keyup', function(e) {
  //   if (e.keyCode === 27) { // Escape key
  //     e.stopPropagation();
  //     closeNavigation(burgerMenu, this);
  //   }
  // });

  // if (userMenu.children.length === 0) {
  //   burgerMenu.style.display = 'none';
  // }

  // Toggles expanded aria to collapsible elements
  var collapsible = document.querySelectorAll('.collapsible-nav, .collapsible-sidebar');

  Array.prototype.forEach.call(collapsible, function(el) {
    var toggle = el.querySelector('.collapsible-nav-toggle, .collapsible-sidebar-toggle');

    el.addEventListener('click', function(e) {
      toggleNavigation(toggle, this);
    });

    el.addEventListener('keyup', function(e) {
      if (e.keyCode === 27) { // Escape key
        closeNavigation(toggle, this);
      }
    });
  });

  // Submit organization form in the request page
  var requestOrganisationSelect = document.querySelector('#request-organization select');

  if (requestOrganisationSelect) {
    requestOrganisationSelect.addEventListener('change', function() {
      closest(this, 'form').submit();
    });
  }

  // If a section has more than 6 subsections, we collapse the list, and show a trigger to display them all
  const seeAllTrigger = document.querySelector("#see-all-sections-trigger");
  const subsectionsList = document.querySelector(".section-list");

  if (subsectionsList && subsectionsList.children.length > 6) {
    seeAllTrigger.setAttribute("aria-hidden", false);

    seeAllTrigger.addEventListener("click", function(e) {
      subsectionsList.classList.remove("section-list--collapsed");
      seeAllTrigger.parentNode.removeChild(seeAllTrigger);
    });
  }

  // If multibrand search has more than 5 help centers or categories collapse the list
  const multibrandFilterLists = document.querySelectorAll(".multibrand-filter-list");
  Array.prototype.forEach.call(multibrandFilterLists, function(filter) {
    if (filter.children.length > 6) {
      // Display the show more button
      var trigger = filter.querySelector(".see-all-filters");
      trigger.setAttribute("aria-hidden", false);

      // Add event handler for click
      trigger.addEventListener("click", function(e) {
        e.stopPropagation();
        trigger.parentNode.removeChild(trigger);
        filter.classList.remove("multibrand-filter-list--collapsed")
      })
    }
  });

  // If there are any error notifications below an input field, focus that field
  const notificationElm = document.querySelector(".notification-error");
  if (
    notificationElm &&
    notificationElm.previousElementSibling &&
    typeof notificationElm.previousElementSibling.focus === "function"
  ) {
    notificationElm.previousElementSibling.focus();
  }
});








/////////////// Added by Crunch ///////////////
const getCategoriesFromApi = async () => {
    const [tmpCategories, tmpSections] = await Promise.all([
        $.getJSON('/api/v2/help_center/en-us/categories.json'),
        $.getJSON('/api/v2/help_center/en-us/sections.json')
    ]);
    const categories = {};
    const categoryPosition = [];
    await tmpCategories.categories.forEach(item => {
        categories[item.id] = item;
        categoryPosition[item.position] = item.id;
        categories[item.id]['sections'] = {};
        categories[item.id]['sectionPosition'] = [];
    });
    await tmpSections.sections.forEach(item => {
        categories[item.category_id]['sections'][item.id] = item;
        categories[item.category_id]['sectionPosition'][item.position] = item.id;
    });
    const retVar = [];
    await categoryPosition.forEach(categoryId => {
        const sections = [];
        for (sectionId of categories[categoryId].sectionPosition) {
            sections.push({
                name: categories[categoryId].sections[sectionId].name,
                url: categories[categoryId].sections[sectionId].html_url,
                id: categories[categoryId].sections[sectionId].id
            })
        }
        retVar.push({
            name: categories[categoryId].name,
            url: categories[categoryId].html_url,
            id: categories[categoryId].id,
            sections
        });
    });
    console.log("Categories from api", retVar);
};
// The purpose of caching categories is to eliminate 2 costly api calls to zendesk on every page view
// if you want to update the category cache then
// 1. Uncomment the following line of code and refresh help desk page in browser
// 2. Review console output
// 3. Right-click the categories from api and choose "store as global variable"
// 4. Enter javascript command "copy(temp1)" to copy array to clipboard
// 5. Paste new categories array above where it says const cachedCategories - ...
// 6. Comment the following line of code
// getCategoriesFromApi();

let cachedCategories = [
    {
        "name": "Getting Started",
        "url": "https://help.crunch.io/hc/en-us/categories/360002564291-Getting-Started",
        "id": 360002564291,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360007708992-Quick-Start",
                "id": 360007708992
            },
            {
                "name": "Browsing Data",
                "url": "https://help.crunch.io/hc/en-us/sections/360007823331-Browsing-Data",
                "id": 360007823331
            },
            {
                "name": "Analyzing Data",
                "url": "https://help.crunch.io/hc/en-us/sections/360007724472-Analyzing-Data",
                "id": 360007724472
            },
            {
                "name": "Deriving Variables",
                "url": "https://help.crunch.io/hc/en-us/sections/360007724492-Deriving-Variables",
                "id": 360007724492
            }
        ]
    },
    {
        "name": "Sharing Data",
        "url": "https://help.crunch.io/hc/en-us/categories/360002558792-Sharing-Data",
        "id": 360002558792,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360007826311-Quick-Start",
                "id": 360007826311
            }
        ]
    },
    {
        "name": "Importing and Cleaning Data",
        "url": "https://help.crunch.io/hc/en-us/categories/360002572271-Importing-and-Cleaning-Data",
        "id": 360002572271,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360007726872-Quick-Start",
                "id": 360007726872
            }
        ]
    },
    {
        "name": "Dataset Properties",
        "url": "https://help.crunch.io/hc/en-us/categories/360002558832-Dataset-Properties",
        "id": 360002558832,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360007726912-Quick-Start",
                "id": 360007726912
            }
        ]
    },
    {
        "name": "How To",
        "url": "https://help.crunch.io/hc/en-us/categories/360002572291-How-To",
        "id": 360002572291,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360007826391-Quick-Start",
                "id": 360007826391
            }
        ]
    },
    {
        "name": "Dashboards",
        "url": "https://help.crunch.io/hc/en-us/categories/360000310512-Dashboards",
        "id": 360000310512,
        "sections": [
            {
                "name": "Quick Start",
                "url": "https://help.crunch.io/hc/en-us/sections/360000683652-Quick-Start",
                "id": 360000683652
            }
        ]
    }
];


const addCategoryMenu = (menuNode) => {
    for (category of cachedCategories) {
        const catNode = document.createElement("li");
        catNode.setAttribute('class', 'nav-item dropdown cr-cat-tab');

        const aNode = document.createElement("a");
        var tabClass = document.URL === category.url ? ' cr-tab-on' : ' cr-tab-off'; 
        aNode.setAttribute('class', 'nav-link cr-cat-tab-label ' + tabClass);
        aNode.setAttribute('href', category.url);
        // aNode.setAttribute('data-toggle', 'dropdown'); // Keeps dropdown down if clicked
        aNode.setAttribute('id', 'navbarDropdown');
        aNode.setAttribute('aria-haspopup', 'true');
        aNode.setAttribute('aria-expanded', 'false');
        aNode.appendChild(document.createTextNode(category.name));

        const bNode = document.createElement("div");
        bNode.setAttribute('class', 'dropdown-menu cr-cat-dropdown-menu');
        bNode.setAttribute('aria-labelledby', 'navbarDropdown');

        for (section of category.sections) {
            const cNode = document.createElement("a");
            cNode.setAttribute('class','dropdown-item');
            cNode.setAttribute('href',section.url);
            cNode.appendChild(document.createTextNode(section.name));
            catNode.appendChild(aNode);
            bNode.appendChild(cNode);
        }
        catNode.appendChild(bNode);
        menuNode.appendChild(catNode);
    }

};


