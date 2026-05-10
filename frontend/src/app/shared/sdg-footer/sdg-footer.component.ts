import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface SDGInfo {
  number: number;
  title: string;
  description: string;
  color: string;
  icon: string;
}

@Component({
  selector: 'app-sdg-footer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sdg-footer.component.html',
  styleUrl: './sdg-footer.component.css'
})
export class SdgFooterComponent {
  @Input() sdgNumber: number = 8; // Default to SDG 8
  @Input() customDescription?: string;

  sdgData: { [key: number]: SDGInfo } = {
    8: {
      number: 8,
      title: 'Decent Work and Economic Growth',
      description: 'Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all.',
      color: '#A21942',
      icon: '💼'
    },
    9: {
      number: 9,
      title: 'Industry, Innovation and Infrastructure',
      description: 'Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation.',
      color: '#DD1C3B',
      icon: '🏭'
    },
    12: {
      number: 12,
      title: 'Responsible Consumption and Production',
      description: 'Ensure sustainable consumption and production patterns.',
      color: '#BF8B2E',
      icon: '♻️'
    },
    15: {
      number: 15,
      title: 'Life on Land',
      description: 'Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification.',
      color: '#56C596',
      icon: '🌍'
    },
    17: {
      number: 17,
      title: 'Partnerships for the Goals',
      description: 'Strengthen the means of implementation and global partnership for sustainable development.',
      color: '#1F4788',
      icon: '🤝'
    }
  };

  get currentSDG(): SDGInfo {
    return this.sdgData[this.sdgNumber] || this.sdgData[8];
  }

  get displayDescription(): string {
    return this.customDescription || this.currentSDG.description;
  }
}
