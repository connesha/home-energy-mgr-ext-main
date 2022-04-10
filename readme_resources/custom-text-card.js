class CustomTextCard extends HTMLElement {
     // Whenever the state changes, a new `hass` object is set. Use this to
    // update your content.
    set hass(hass) {
      // Initialize the content if it's not there yet.
      if (!this.content) {
        this.innerHTML = `
          <ha-card header="">
            <div class="card-content"></div>
         </ha-card>
        `;
        this.content = this.querySelector('div');
      }

      // const display_text = this.config.display-text;
      const entity_dis = this.config.entity;
      const display_text = this.config.display_text;
      const display_font_size = this.config.display_font_size;
      const display_font_color = this.config.display_font_color;

      this.content.innerHTML = `
        <font color="${display_font_color}" size=${display_font_size}>${display_text}</font>
      `;
    }

    // The user supplied configuration. Throw an exception and Lovelace will
    // render an error card.
    setConfig(config) {
      this.config = config;
    }

    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns.
    getCardSize() {
      return 1;
    }
  }

  customElements.define('custom-text-card', CustomTextCard);