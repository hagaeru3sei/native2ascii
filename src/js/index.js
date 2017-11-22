import Vue from 'vue/dist/vue'
import axios from 'axios'
import downloadjs from 'downloadjs'
import Vuetable from 'vuetable-2/src/components/Vuetable.vue'
import VuetablePagination from 'vuetable-2/src/components/VuetablePagination.vue'
import VueEvents from 'vue-events'
import config from 'config'

Vue.use(Vuetable);
Vue.use(VueEvents);

const msg = "Convert native2ascii for java apps";
const languageEndpoint = config.languageEndpoint;
const endpoint = config.endpoint;
const bus = new Vue();

function getLanguageCodes() {
  let languages = [];
  axios.get(languageEndpoint).then(res => {
    console.log(res);
    languages = res.data.languages
  });
  console.log(languages);
  return languages;
}

function timestamp2datetime(timestamp) {
  let d = new Date(timestamp * 1000);
  return d.toISOString().replace("T", " ").replace(/\.[0-9]*Z$/, "")
}


// attach message
new Vue({
  data : {
    message: msg
  }
}).$mount('#message');


// Set languages
const formApp = new Vue({
  el: '#newRecordForm',
  data: {
    /**
     * example:
     *   ['en', 'jp']
     */
    languages: [],

    /**
     * example:
     *   {
     *     'en': {
     *       'key': '',
     *       'value': '',
     *       'description': ''
     *     },,,
     *   }
     */
    jsonRequest : {}
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  computed: {
    keyName: function (name, lang) {
      return name + "_" + lang
    }
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log(res);
        this.languages = res.data.languages
      });
    },
    addNewRecord: function () {
      console.log("Called addNewRecord.");
      console.log(this);
      let items = {};
      [].slice.call(Object.keys(this.jsonRequest)).forEach(lang => {
         let item = this.jsonRequest[lang];
         items[lang] = {
           key: item.key,
           value: item.value,
           description: item.description
         }
      });
      console.log("JSON string:", JSON.stringify(items));
      axios.post(endpoint, items).then(response => {
        console.log(response)
      });
      this.$emit('update.record', true)
    }
  }
});

// download property file
const downloadApp = new Vue({
  el: "#downloadForm",
  data: {
    selectedLanguage: 'en',
    languages: []
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log("GET /lang response", res);
        this.languages = res.data.languages
      });
    },
    download: function () {
      axios.get(endpoint + "/dl/" + this.selectedLanguage).then(response => {
        console.log("response:", response);
        downloadjs(response.data, 'message_' + this.selectedLanguage + '.properties')
      })
    }
  }
});

// upload property file
const uploadApp = new Vue({
  el : '#uploadForm',
  data: {
    selectedLanguage: 'en',
    languages: [],
    language: 'en',
    file: null
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log("GET /lang response", res);
        this.languages = res.data.languages
      });
    },
    selectedFile: function(event) {
      console.log("selectedFile");
      event.preventDefault();
      let files = event.target.files || event.dataTransfer.files;
      if (!files.length) {
        return;
      }
      this.file = files[0]
    },
    upload: function () {
      console.log("upload method called");
      let formData = new FormData();
      formData.append('property_file', this.file);
      formData.append('language', this.language);
      let config = {
        headers : {
          'content-type' : 'multipart/form-data'
        }
      };
      let url = endpoint + '/upload/' + this.selectedLanguage;
      axios.post(url, formData, config).then(res => {
        console.log("response", res)
      }).catch(e =>
        console.log("error", e)
      );
    }
  }
});

// controller
new Vue({
  el : '#controlPanel',
  data : {

  },
  components : {
    'add-component' : formApp,
    'download-component' : downloadApp,
    'upload-component' : uploadApp
  },
  methods : {
    /**
     *
     * @param componentName
     * @param type (none|block)
     */
    changeDisplay: function(componentName, type) {
      let component = this.$options.components[componentName];
      //console.log(component);
      if (typeof component === 'undefined') return;
      let style = component.$el.style;
      style.display = type;
    },
    add : function () {
      this.changeDisplay('add-component', 'block');
      this.changeDisplay('upload-component', 'none');
      this.changeDisplay('download-component', 'none');
    },
    upload : function () {
      this.changeDisplay('add-component', 'none');
      this.changeDisplay('upload-component', 'block');
      this.changeDisplay('download-component', 'none');
    },
    download : function () {
      this.changeDisplay('add-component', 'none');
      this.changeDisplay('upload-component', 'none');
      this.changeDisplay('download-component', 'block');
    }
  }
});

// Edit record
const editTable = new Vue({
  el : '#editTable',
  data: {
    language : '',
    key : '',
    value : '',
    description : ''
  },
  methods : {
    cancel() {
      this.$el.style.display = 'none';
    },
    update : function () {
      let items = {};
      items[this.language] = {
        key: this.key,
        value: this.value,
        description: this.description
      };
      axios.post(endpoint, items).then(response => {
        console.log(response);
        this.$el.style.display = 'none';
        // emit reload
        bus.$emit('reload-table')
      }).catch(e => {
        console.log(e);
        this.$el.style.display = 'none';
      });
    }
  }
});

const searchForm = new Vue({
  el: "#searchForm",
  data () {
    return {
      filterText: ''
    }
  },
  methods: {
    doFilter() {
      console.log("doFilter", this.filterText);
      this.$events.fire('filter-set', this.filterText)
    },
    resetFilter() {
      this.filterText = '';
      console.log('resetFilter')
    }
  }
});

// vuetable-2
new Vue({
  el: '#app',
  components: {
    'vuetable' : Vuetable,
    'vuetable-pagination': VuetablePagination,
    'edit-table' : editTable
  },
  data: {
    endpoint: endpoint,
    fields: [
      {
        name: 'id',
        title: 'id',
        sortField: 'id'
      },
      {
        name: 'language',
        title: 'Language',
        sortField: 'language'
      },
      {
        name: 'key',
        title: 'key',
        sortField: 'key'
      },
      'value',
      'description',
      {
        name: 'updated',
        title: 'Updated',
        sortField: 'updated',
        callback: timestamp2datetime
      },
      '__slot:actions'
    ],
    sortOrder: [
      { field: 'id', direction: 'asc' }
    ],
    moreParams: {

    },
    css: {
      table: {
        tableClass: 'table table-striped table-bordered table-hovered',
        loadingClass: 'loading',
        ascendingIcon: 'glyphicon glyphicon-chevron-up',
        descendingIcon: 'glyphicon glyphicon-chevron-down',
        handleIcon: 'glyphicon glyphicon-menu-hamburger',
      },
      pagination: {
        infoClass: 'pull-left',
        wrapperClass: 'vuetable-pagination pull-right',
        activeClass: 'btn-primary',
        disabledClass: 'disabled',
        pageClass: 'btn btn-border',
        linkClass: 'btn btn-border',
        icons: {
          first: '',
          prev: '',
          next: '',
          last: '',
        },
      }
    }
  },
  methods: {
    /**
     *
     * @param paginationData
     */
    onPaginationData(paginationData) {
      this.$refs.pagination.setPaginationData(paginationData)
    },
    /**
     *
     * @param page
     */
    onChangePage(page) {
      this.$refs.vuetable.changePage(page)
    },
    /**
     *
     * @param rowData
     */
    editRow(rowData) {
      console.log("edit: "+ JSON.stringify(rowData));
      let component = this.$options.components['edit-table'];
      component.language = rowData.language;
      component.key = rowData.key;
      component.value = rowData.value;
      component.description = rowData.description;
      console.log("editTable component:", component);
      component.$el.style.display = '-webkit-flex';
      component.$el.style.display = 'flex';
    },
    /**
     *
     * @param rowData
     */
    deleteRow(rowData) {
      let config = {
        headers : {}
      };
      console.log("delete: "+ JSON.stringify(rowData));
      axios.delete(endpoint + "?id=" + rowData['id'], config).then(response => {
        console.log(response);
        this.$refs.vuetable.reload()
      }).catch(e => {
        console.log(e)
      });
    },
    /**
     *
     */
    reloadTable() {
      console.log("reload table");
      this.$refs.vuetable.reload();
    },
    /**
     *
     */
    onLoading() {
      console.log('loading...')
    },
    /**
     *
     */
    onLoaded() {
      console.log('loaded!')
    },
    /**
     *
     * @param filterText
     */
    onFilterSet(filterText) {
      console.log('onFilterSet', filterText, this);
      this.moreParams = {
        'filter': filterText
      };
      Vue.nextTick(() => this.$refs.vuetable.refresh())
    }
  },
  mounted: function() {
    console.log("mounted");
    // reload event
    let v = this.$refs.vuetable;
    bus.$on('reload-table', function() {
      v.reload()
    });

    // filter event
    this.$events.$on('filter-set', eventData => this.onFilterSet(eventData))
  }
});
